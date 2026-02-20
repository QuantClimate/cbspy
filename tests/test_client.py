import httpx
import polars as pl
import pytest
import respx

from cbspy.client import Client
from cbspy.exceptions import TableNotFoundError
from cbspy.models import Column, TableMetadata

BASE = "https://opendata.cbs.nl"


class TestListTables:
    @respx.mock
    def test_returns_polars_dataframe(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(200, json={
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
            })
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
            return_value=httpx.Response(200, json={
                "value": [
                    {"Identifier": "37296eng", "Title": "Pop", "ShortDescription": "",
                     "Period": "", "Frequency": "", "RecordCount": 1, "Modified": "", "Language": "en"},
                ]
            })
        )
        client = Client()
        df = client.list_tables(language="en")
        assert df.shape[0] == 1


class TestGetMetadata:
    @respx.mock
    def test_returns_table_metadata(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TableInfos").mock(
            return_value=httpx.Response(200, json={
                "value": [{
                    "Title": "Population; key figures",
                    "ShortDescription": "A description.",
                    "Identifier": "37296eng",
                    "Period": "1950 - 2022",
                    "Frequency": "Perjaar",
                }]
            })
        )
        respx.get(f"{BASE}/ODataApi/odata/37296eng/DataProperties").mock(
            return_value=httpx.Response(200, json={
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
            })
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
        respx.get(f"{BASE}/ODataApi/odata/FAKE/TableInfos").mock(
            return_value=httpx.Response(404, text="Not found")
        )
        client = Client()
        with pytest.raises(TableNotFoundError):
            client.get_metadata("FAKE")
