from __future__ import annotations

import time
from typing import Any

import httpx

from cbspy.exceptions import APIError, TableNotFoundError

_ODATA_API = "/ODataApi/odata"
_CATALOG = "/ODataCatalog/Tables"

_MAX_RETRIES = 1
_RETRY_DELAY = 1.0


class ODataClient:
    """Low-level OData HTTP client for CBS Statline."""

    def __init__(self, base_url: str, http_client: httpx.Client) -> None:
        self._base_url = base_url.rstrip("/")
        self._http = http_client

    def get_json(self, table_id: str, resource: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        """Fetch a resource for a table, following pagination."""
        url = f"{self._base_url}{_ODATA_API}/{table_id}/{resource}"
        request_params = {"$format": "json"}
        if params:
            request_params.update(params)

        all_rows: list[dict[str, Any]] = []

        while url is not None:
            response = self._request_with_retry(url, request_params, table_id)

            body = response.json()
            all_rows.extend(body.get("value", []))

            url = body.get("odata.nextLink")
            request_params = {}  # nextLink includes all params

        return all_rows

    def get_catalog(self, language: str | None = None) -> list[dict[str, Any]]:
        """Fetch the CBS table catalog."""
        url = f"{self._base_url}{_CATALOG}"
        params: dict[str, str] = {"$format": "json"}

        if language:
            lang_code = "en" if language == "en" else "nl"
            params["$filter"] = f"Language eq '{lang_code}'"

        all_rows: list[dict[str, Any]] = []

        while url is not None:
            response = self._request_with_retry(url, params, "catalog")

            body = response.json()
            all_rows.extend(body.get("value", []))

            url = body.get("odata.nextLink")
            params = {}

        return all_rows

    def _request_with_retry(self, url: str, params: dict[str, str], table_id: str) -> httpx.Response:
        """Make an HTTP GET with retry on transient errors."""
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = self._http.get(url, params=params)
            except httpx.RequestError:
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY)
                    continue
                raise

            if response.status_code == 404:
                msg = f"Table '{table_id}' not found. Use client.list_tables() to discover available tables."
                raise TableNotFoundError(msg)

            if response.status_code >= 500 and attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)
                continue

            if response.status_code >= 400:
                raise APIError(status_code=response.status_code, message=response.text)

            return response

        # Should not reach here, but satisfy type checker
        raise APIError(status_code=response.status_code, message=response.text)
