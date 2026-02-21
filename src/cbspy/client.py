from __future__ import annotations

from typing import Any

import httpx
import polars as pl

from cbspy._odata import ODataClient
from cbspy._periods import decode_period
from cbspy.models import Column, TableMetadata

_DEFAULT_BASE_URL = "https://opendata.cbs.nl"


class Client:
    """CBS Statline open data client.

    Args:
        base_url: CBS OData API base URL. Override for testing.
        http_client: Custom httpx.Client instance. Created automatically if not provided.
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client()
        self._odata = ODataClient(base_url=base_url, http_client=self._http)

    def close(self) -> None:
        """Close the underlying HTTP client if this instance owns it."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def list_tables(self, language: str | None = None) -> pl.DataFrame:
        """List available CBS tables.

        Args:
            language: Filter by language ("en" or "nl"). Returns all if None.

        Returns:
            Polars DataFrame with columns: id, title, description, period,
            frequency, record_count, modified.
        """
        rows = self._odata.get_catalog(language=language)
        return pl.DataFrame({
            "id": [r["Identifier"] for r in rows],
            "title": [r["Title"] for r in rows],
            "description": [r.get("ShortDescription", "") for r in rows],
            "period": [r.get("Period", "") for r in rows],
            "frequency": [r.get("Frequency", "") for r in rows],
            "record_count": [r.get("RecordCount", 0) for r in rows],
            "modified": [r.get("Modified", "") for r in rows],
        })

    def get_metadata(self, table_id: str) -> TableMetadata:
        """Get metadata and column definitions for a CBS table.

        Args:
            table_id: CBS table identifier (e.g. "37296eng").

        Returns:
            TableMetadata with column properties.
        """
        info_rows = self._odata.get_json(table_id, "TableInfos")
        info = info_rows[0]

        prop_rows = self._odata.get_json(table_id, "DataProperties")
        columns = [self._parse_column(p) for p in prop_rows]

        return TableMetadata(
            id=info.get("Identifier", table_id),
            title=info.get("Title", ""),
            description=info.get("ShortDescription", ""),
            period=info.get("Period", ""),
            frequency=info.get("Frequency", ""),
            properties=columns,
        )

    def get_data(
        self,
        table_id: str,
        periods: list[str] | None = None,
        filters: dict[str, list[str]] | str | None = None,
        columns: list[str] | None = None,
    ) -> pl.DataFrame:
        """Fetch dataset as a Polars DataFrame with human-readable column names.

        Args:
            table_id: CBS table identifier (e.g. "37296eng").
            periods: Optional list of CBS period codes to filter by.
            filters: Optional dimension filters. Either a raw OData $filter string
                or a dict mapping dimension keys to value lists, e.g.
                ``{"RegioS": ["GM0363", "GM0599"]}``.
            columns: Optional list of columns to retrieve. Accepts human-readable
                names (e.g. "Total population") or CBS keys (e.g. "TotalPopulation_1").
                Fetches all columns if None.

        Returns:
            Polars DataFrame with resolved column names and decoded periods.
        """
        prop_rows = self._odata.get_json(table_id, "DataProperties")
        column_map = {p["Key"]: p.get("Title", p["Key"]) for p in prop_rows}
        period_keys = {p["Key"] for p in prop_rows if p.get("Type") == "TimeDimension"}

        filter_str = self._build_filter(periods, filters, period_keys)
        params: dict[str, str] = {}
        if filter_str:
            params["$filter"] = filter_str

        if columns is not None:
            title_to_key = {v: k for k, v in column_map.items()}
            select_keys = [title_to_key.get(c, c) for c in columns]
            params["$select"] = ",".join(select_keys)

        data_rows = self._odata.get_json(table_id, "TypedDataSet", params=params or None)

        if not data_rows:
            empty_cols = {column_map.get(k, k): [] for k in column_map}
            return pl.DataFrame(empty_cols)

        renamed_rows = []
        for row in data_rows:
            renamed: dict[str, Any] = {}
            for key, value in row.items():
                if key == "ID":
                    continue
                new_key = column_map.get(key, key)
                if key in period_keys:
                    value = decode_period(str(value))
                renamed[new_key] = value
            renamed_rows.append(renamed)

        return pl.DataFrame(renamed_rows)

    @staticmethod
    def _build_filter(
        periods: list[str] | None,
        filters: dict[str, list[str]] | str | None,
        period_keys: set[str],
    ) -> str:
        """Compile periods and filters into an OData $filter string."""
        parts: list[str] = []

        if periods and period_keys:
            period_key = next(iter(period_keys))
            clause = " or ".join(f"{period_key} eq '{p}'" for p in periods)
            parts.append(f"({clause})")

        if isinstance(filters, str):
            parts.append(filters)
        elif isinstance(filters, dict):
            for dim, values in filters.items():
                clause = " or ".join(f"{dim} eq '{v}'" for v in values)
                parts.append(f"({clause})")

        return " and ".join(parts)

    @staticmethod
    def _parse_column(prop: dict[str, Any]) -> Column:
        """Convert a raw DataProperties entry to a Column model."""
        return Column(
            id=prop.get("Key", ""),
            name=prop.get("Title", ""),
            unit=prop.get("Unit", ""),
            datatype=prop.get("Datatype", prop.get("Type", "")),
            description=prop.get("Description", ""),
        )
