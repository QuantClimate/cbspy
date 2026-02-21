import httpx
import polars as pl
import pytest
import respx

from cbspy.client import Client
from cbspy.exceptions import TableNotFoundError
from cbspy.models import TableMetadata

BASE = "https://opendata.cbs.nl"


def test_public_imports():
    from cbspy import APIError, CBSError, Client, Column, TableMetadata, TableNotFoundError

    assert Client is not None
    assert Column is not None
    assert TableMetadata is not None
    assert CBSError is not None
    assert TableNotFoundError is not None
    assert APIError is not None


class TestListTables:
    @respx.mock
    def test_returns_polars_dataframe(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Identifier": "37296eng",
                            "Title": "Population; key figures",
                            "ShortDescription": "Population stats",
                            "Period": "1950 - 2022",
                            "Frequency": "Perjaar",
                            "RecordCount": 73,
                            "Modified": "2023-04-12T02:00:00",
                            "Language": "en",
                        }
                    ]
                },
            )
        )
        client = Client()
        df = client.list_tables()
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (1, 7)
        assert df.columns == ["id", "title", "description", "period", "frequency", "record_count", "modified"]
        assert df["id"][0] == "37296eng"

    @respx.mock
    def test_filters_by_language(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Identifier": "37296eng",
                            "Title": "Pop",
                            "ShortDescription": "",
                            "Period": "",
                            "Frequency": "",
                            "RecordCount": 1,
                            "Modified": "",
                            "Language": "en",
                        },
                    ]
                },
            )
        )
        client = Client()
        df = client.list_tables(language="en")
        assert df.shape[0] == 1


class TestGetMetadata:
    @respx.mock
    def test_returns_table_metadata(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/TableInfos").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Title": "Population; key figures",
                            "ShortDescription": "A description.",
                            "Identifier": "37296eng",
                            "Period": "1950 - 2022",
                            "Frequency": "Perjaar",
                        }
                    ]
                },
            )
        )
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "odata.type": "Cbs.OData.TimeDimension",
                            "ID": 0,
                            "Key": "Periods",
                            "Title": "Periods",
                            "Description": "Time periods",
                            "Type": "TimeDimension",
                        },
                        {
                            "odata.type": "Cbs.OData.Topic",
                            "ID": 1,
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Description": "The total population.",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        client = Client()
        meta = client.get_metadata("37296eng")
        assert isinstance(meta, TableMetadata)
        assert meta.id == "37296eng"
        assert meta.title == "Population; key figures"
        assert len(meta.properties) == 2
        assert meta.properties[1].id == "TotalPopulation_1"
        assert meta.properties[1].name == "Total population"
        assert meta.properties[1].datatype == "Double"

    @respx.mock
    def test_not_found_raises(self):
        respx.get(f"{BASE}/ODataFeed/OData/FAKE/TableInfos").mock(return_value=httpx.Response(404, text="Not found"))
        client = Client()
        with pytest.raises(TableNotFoundError):
            client.get_metadata("FAKE")


class TestGetData:
    @respx.mock
    def test_returns_dataframe_with_resolved_columns(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "odata.type": "Cbs.OData.TimeDimension",
                            "ID": 0,
                            "Key": "Periods",
                            "Title": "Periods",
                            "Description": "",
                            "Type": "TimeDimension",
                        },
                        {
                            "odata.type": "Cbs.OData.Topic",
                            "ID": 1,
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Description": "",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                        {
                            "odata.type": "Cbs.OData.Topic",
                            "ID": 2,
                            "Key": "Males_2",
                            "Title": "Males",
                            "Description": "",
                            "Type": "Topic",
                            "Datatype": "Long",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291, "Males_2": 8864},
                        {"ID": 1, "Periods": "2022JJ00", "TotalPopulation_1": 17590672, "Males_2": 8757},
                    ]
                },
            )
        )
        client = Client()
        df = client.get_data("37296eng")
        assert isinstance(df, pl.DataFrame)
        assert "Periods" in df.columns
        assert "Total population" in df.columns
        assert "Males" in df.columns
        assert df["Periods"][0] == "2023"
        assert df["Total population"][0] == 17811291

    @respx.mock
    def test_get_data_with_periods_filter(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "odata.type": "Cbs.OData.TimeDimension",
                            "ID": 0,
                            "Key": "Periods",
                            "Title": "Periods",
                            "Description": "",
                            "Type": "TimeDimension",
                        },
                        {
                            "odata.type": "Cbs.OData.Topic",
                            "ID": 1,
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Description": "",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291},
                    ]
                },
            )
        )
        client = Client()
        df = client.get_data("37296eng", periods=["2023JJ00"])
        assert df.shape[0] == 1

    @respx.mock
    def test_get_data_empty_dataset(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "odata.type": "Cbs.OData.TimeDimension",
                            "ID": 0,
                            "Key": "Periods",
                            "Title": "Periods",
                            "Description": "",
                            "Type": "TimeDimension",
                        },
                    ]
                },
            )
        )
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={"value": []})
        )
        client = Client()
        df = client.get_data("37296eng")
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 0


class TestClientLifecycle:
    def test_close_closes_owned_http_client(self):
        client = Client()
        assert not client._http.is_closed
        client.close()
        assert client._http.is_closed

    def test_close_does_not_close_external_http_client(self):
        http = httpx.Client()
        client = Client(http_client=http)
        client.close()
        assert not http.is_closed
        http.close()

    def test_context_manager(self):
        with Client() as client:
            assert not client._http.is_closed
        assert client._http.is_closed

    def test_context_manager_with_external_client(self):
        http = httpx.Client()
        with Client(http_client=http) as client:
            assert not client._http.is_closed
        assert not http.is_closed
        http.close()
