import httpx
import pytest
import respx

from cbspy._odata import ODataClient
from cbspy.exceptions import APIError, TableNotFoundError

BASE = "https://opendata.cbs.nl"


class TestGetJson:
    @respx.mock
    def test_returns_value_array(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={"value": [{"ID": 0, "Periods": "2023JJ00"}]})
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0, "Periods": "2023JJ00"}]

    def test_follows_pagination(self):
        page1 = httpx.Response(
            200,
            json={
                "value": [{"ID": 0}],
                "odata.nextLink": f"{BASE}/ODataApi/odata/37296eng/TypedDataSet?$skip=1",
            },
        )
        page2 = httpx.Response(
            200,
            json={
                "value": [{"ID": 1}],
            },
        )
        responses = iter([page1, page2])
        transport = httpx.MockTransport(lambda req: next(responses))
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0}, {"ID": 1}]

    @respx.mock
    def test_404_raises_table_not_found(self):
        respx.get(f"{BASE}/ODataApi/odata/FAKE/TypedDataSet").mock(return_value=httpx.Response(404, text="Not found"))
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        with pytest.raises(TableNotFoundError):
            client.get_json("FAKE", "TypedDataSet")

    @respx.mock
    def test_500_raises_api_error(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        with pytest.raises(APIError) as exc_info:
            client.get_json("37296eng", "TypedDataSet")
        assert exc_info.value.status_code == 500


class TestGetCatalog:
    @respx.mock
    def test_returns_table_catalog(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(200, json={"value": [{"Identifier": "37296eng", "Title": "Population"}]})
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_catalog()
        assert result == [{"Identifier": "37296eng", "Title": "Population"}]

    @respx.mock
    def test_catalog_with_language_filter(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Identifier": "37296eng", "Title": "Population", "Language": "en"},
                    ]
                },
            )
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_catalog(language="en")
        assert len(result) == 1
        assert result[0]["Language"] == "en"


class TestRetryBehavior:
    def test_retries_once_on_500_then_succeeds(self):
        attempt = 0

        def handler(request):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                return httpx.Response(500, text="Internal Server Error")
            return httpx.Response(200, json={"value": [{"ID": 0}]})

        transport = httpx.MockTransport(handler)
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0}]
        assert attempt == 2

    def test_raises_after_retry_exhausted(self):
        def handler(request):
            return httpx.Response(503, text="Service Unavailable")

        transport = httpx.MockTransport(handler)
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        with pytest.raises(APIError) as exc_info:
            client.get_json("37296eng", "TypedDataSet")
        assert exc_info.value.status_code == 503

    def test_no_retry_on_404(self):
        attempt = 0

        def handler(request):
            nonlocal attempt
            attempt += 1
            return httpx.Response(404, text="Not found")

        transport = httpx.MockTransport(handler)
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        with pytest.raises(TableNotFoundError):
            client.get_json("FAKE", "TypedDataSet")
        assert attempt == 1

    def test_retries_on_network_error_then_succeeds(self):
        attempt = 0

        def handler(request):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise httpx.ConnectError("Connection refused")  # noqa: TRY003
            return httpx.Response(200, json={"value": [{"ID": 0}]})

        transport = httpx.MockTransport(handler)
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0}]
        assert attempt == 2

    def test_raises_network_error_after_retry_exhausted(self):
        def handler(request):
            raise httpx.ConnectError("Connection refused")  # noqa: TRY003

        transport = httpx.MockTransport(handler)
        client = ODataClient(base_url=BASE, http_client=httpx.Client(transport=transport))
        with pytest.raises(httpx.ConnectError):
            client.get_json("37296eng", "TypedDataSet")
