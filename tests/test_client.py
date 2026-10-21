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

    @respx.mock
    def test_null_fields_become_empty_strings(self):
        # CBS sends explicit nulls, e.g. 86103NED has properties with "Description": null.
        respx.get(f"{BASE}/ODataFeed/OData/86103NED/TableInfos").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Title": "Aardgasbalans; aanbod en verbruik",
                            "ShortDescription": None,
                            "Identifier": "86103NED",
                            "Period": "2015 - augustus 2026",
                            "Frequency": None,
                        }
                    ]
                },
            )
        )
        respx.get(f"{BASE}/ODataFeed/OData/86103NED/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "ID": 0,
                            "Key": "Perioden",
                            "Title": "Perioden",
                            "Description": None,
                            "Type": "TimeDimension",
                            "Unit": None,
                        },
                        {
                            "ID": 1,
                            "Key": "TotaalVerbruik_25",
                            "Title": "Totaal verbruik",
                            "Description": None,
                            "Type": "Topic",
                            "Datatype": "Long",
                            "Unit": "mln m3",
                        },
                    ]
                },
            )
        )
        client = Client()
        meta = client.get_metadata("86103NED")
        assert meta.description == ""
        assert meta.frequency == ""
        assert meta.properties[0].unit == ""
        assert meta.properties[1].description == ""
        assert meta.properties[1].unit == "mln m3"


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

    def _mock_long_table(self, values: list[float | int | None]) -> None:
        respx.get(f"{BASE}/ODataFeed/OData/00372/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Perioden", "Title": "Perioden", "Type": "TimeDimension"},
                        {"Key": "Invoer_1", "Title": "Invoer", "Type": "Topic", "Datatype": "Double"},
                    ]
                },
            )
        )
        rows = [{"ID": i, "Perioden": f"{1900 + i}JJ00", "Invoer_1": v} for i, v in enumerate(values)]
        respx.get(f"{BASE}/ODataFeed/OData/00372/TypedDataSet").mock(
            return_value=httpx.Response(200, json={"value": rows})
        )

    @respx.mock
    def test_column_null_for_first_hundred_rows(self):
        # Long CBS tables (e.g. 00372, from 1946) often have series that start late.
        self._mock_long_table([None] * 100 + [100])
        df = Client().get_data("00372")
        assert df["Invoer"][-1] == 100

    @respx.mock
    def test_float_after_hundred_ints_is_not_truncated(self):
        self._mock_long_table([1] * 100 + [1.5])
        df = Client().get_data("00372")
        assert df["Invoer"][-1] == 1.5

    """Tests for the generic filters parameter on get_data()."""

    def _mock_props(self):
        """Mock DataProperties with a time dimension and a geo dimension."""
        respx.get(f"{BASE}/ODataFeed/OData/71450ned/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Perioden", "Title": "Periods", "Type": "TimeDimension"},
                        {"Key": "RegioS", "Title": "Region", "Type": "GeoDimension"},
                        {
                            "Key": "Bevolking_1",
                            "Title": "Population",
                            "Type": "Topic",
                            "Datatype": "Long",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )

    @respx.mock
    def test_filters_dict_single_dimension(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            df = client.get_data("71450ned", filters={"RegioS": ["GM0363"]})
        assert df.shape[0] == 1
        sent_params = dict(route.calls[0].request.url.params)
        assert "$filter" in sent_params
        assert "RegioS" in sent_params["$filter"]

    @respx.mock
    def test_filters_dict_multiple_dimensions(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            client.get_data("71450ned", filters={"RegioS": ["GM0363"], "Perioden": ["2023JJ00"]})
        sent_params = dict(route.calls[0].request.url.params)
        filter_str = sent_params["$filter"]
        assert "RegioS" in filter_str
        assert "Perioden" in filter_str

    @respx.mock
    def test_filters_raw_string(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            client.get_data("71450ned", filters="RegioS eq 'GM0363'")
        sent_params = dict(route.calls[0].request.url.params)
        assert sent_params["$filter"] == "RegioS eq 'GM0363'"

    @respx.mock
    def test_periods_param_still_works(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            client.get_data("71450ned", periods=["2023JJ00"])
        sent_params = dict(route.calls[0].request.url.params)
        assert "Perioden" in sent_params["$filter"]

    @respx.mock
    def test_filters_and_periods_combined(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            client.get_data("71450ned", periods=["2023JJ00"], filters={"RegioS": ["GM0363"]})
        sent_params = dict(route.calls[0].request.url.params)
        filter_str = sent_params["$filter"]
        assert "RegioS" in filter_str
        assert "Perioden" in filter_str

    @respx.mock
    def test_no_filters(self):
        self._mock_props()
        route = respx.get(f"{BASE}/ODataFeed/OData/71450ned/TypedDataSet").mock(
            return_value=httpx.Response(
                200, json={"value": [{"ID": 0, "Perioden": "2023JJ00", "RegioS": "GM0363    ", "Bevolking_1": 921402}]}
            )
        )
        with Client() as client:
            client.get_data("71450ned")
        sent_params = dict(route.calls[0].request.url.params)
        assert "$filter" not in sent_params


class TestGetDataColumns:
    """Tests for the columns ($select) parameter on get_data()."""

    @respx.mock
    def test_columns_sends_select_param(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                        {"Key": "Males_2", "Title": "Males", "Type": "Topic", "Datatype": "Long", "Unit": "number"},
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291}]},
            )
        )
        with Client() as client:
            client.get_data("37296eng", columns=["Periods", "Total population"])
        sent_params = dict(route.calls[0].request.url.params)
        assert "$select" in sent_params
        select_val = sent_params["$select"]
        assert "Periods" in select_val
        assert "TotalPopulation_1" in select_val
        assert "Males_2" not in select_val

    @respx.mock
    def test_columns_with_cbs_keys(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291}]},
            )
        )
        with Client() as client:
            client.get_data("37296eng", columns=["Periods", "TotalPopulation_1"])
        sent_params = dict(route.calls[0].request.url.params)
        assert "TotalPopulation_1" in sent_params["$select"]

    @respx.mock
    def test_columns_none_sends_no_select(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291}]},
            )
        )
        with Client() as client:
            client.get_data("37296eng")
        sent_params = dict(route.calls[0].request.url.params)
        assert "$select" not in sent_params


class TestGetDataUntyped:
    """Tests for typed=False (UntypedDataSet) support."""

    @respx.mock
    def test_typed_false_fetches_untyped_dataset(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/UntypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": "."}]},
            )
        )
        with Client() as client:
            df = client.get_data("37296eng", typed=False)
        assert df["Total population"][0] == "."
        assert route.called

    @respx.mock
    def test_typed_true_fetches_typed_dataset(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291}]},
            )
        )
        with Client() as client:
            client.get_data("37296eng", typed=True)
        assert route.called

    @respx.mock
    def test_typed_default_is_true(self):
        respx.get(f"{BASE}/ODataFeed/OData/37296eng/DataProperties").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [
                        {"Key": "Periods", "Title": "Periods", "Type": "TimeDimension"},
                        {
                            "Key": "TotalPopulation_1",
                            "Title": "Total population",
                            "Type": "Topic",
                            "Datatype": "Double",
                            "Unit": "number",
                        },
                    ]
                },
            )
        )
        route = respx.get(f"{BASE}/ODataFeed/OData/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(
                200,
                json={"value": [{"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291}]},
            )
        )
        with Client() as client:
            client.get_data("37296eng")
        assert route.called


GROUPED_PROPS = [
    {"ID": 0, "Key": "Perioden", "Title": "Perioden", "Type": "TimeDimension"},
    {"ID": 1, "Key": "", "Title": "Aardgas", "Type": "TopicGroup"},
    {"ID": 2, "ParentID": 1, "Key": "Transporttarief_1", "Title": "Transporttarief", "Type": "Topic"},
    {"ID": 3, "Key": "", "Title": "Elektriciteit", "Type": "TopicGroup"},
    {"ID": 4, "ParentID": 3, "Key": "Transporttarief_7", "Title": "Transporttarief", "Type": "Topic"},
    {"ID": 5, "ParentID": 3, "Key": "Vermindering_15", "Title": "Vermindering energiebelasting", "Type": "Topic"},
]


class TestGetDataDuplicateTitles:
    """Columns that share a title, e.g. 85592NED has "Transporttarief" under both Aardgas and Elektriciteit."""

    def _mock_props(self, props: list[dict]) -> None:
        respx.get(f"{BASE}/ODataFeed/OData/85592NED/DataProperties").mock(
            return_value=httpx.Response(200, json={"value": props})
        )

    def _mock_rows(self, rows: list[dict]) -> respx.Route:
        return respx.get(f"{BASE}/ODataFeed/OData/85592NED/TypedDataSet").mock(
            return_value=httpx.Response(200, json={"value": rows})
        )

    @respx.mock
    def test_shared_titles_are_qualified_by_group(self):
        self._mock_props(GROUPED_PROPS)
        self._mock_rows([
            {
                "ID": 0,
                "Perioden": "2026MM09",
                "Transporttarief_1": 221.79,
                "Transporttarief_7": 394.11,
                "Vermindering_15": -519.8,
            }
        ])
        with Client() as client:
            df = client.get_data("85592NED")
        assert df.columns == [
            "Perioden",
            "Aardgas: Transporttarief",
            "Elektriciteit: Transporttarief",
            "Vermindering energiebelasting",
        ]
        assert df["Aardgas: Transporttarief"][0] == 221.79
        assert df["Elektriciteit: Transporttarief"][0] == 394.11

    @respx.mock
    def test_shared_titles_without_group_fall_back_to_key(self):
        self._mock_props([
            {"Key": "Perioden", "Title": "Perioden", "Type": "TimeDimension"},
            {"Key": "Totaal_1", "Title": "Totaal", "Type": "Topic"},
            {"Key": "Totaal_2", "Title": "Totaal", "Type": "Topic"},
        ])
        self._mock_rows([{"ID": 0, "Perioden": "2026MM09", "Totaal_1": 1, "Totaal_2": 2}])
        with Client() as client:
            df = client.get_data("85592NED")
        assert df["Totaal (Totaal_1)"][0] == 1
        assert df["Totaal (Totaal_2)"][0] == 2

    @respx.mock
    def test_columns_accepts_qualified_title(self):
        self._mock_props(GROUPED_PROPS)
        route = self._mock_rows([{"ID": 0, "Perioden": "2026MM09", "Transporttarief_1": 221.79}])
        with Client() as client:
            client.get_data("85592NED", columns=["Perioden", "Aardgas: Transporttarief"])
        assert dict(route.calls[0].request.url.params)["$select"] == "Perioden,Transporttarief_1"

    @respx.mock
    def test_columns_rejects_shared_title(self):
        self._mock_props(GROUPED_PROPS)
        with Client() as client, pytest.raises(ValueError, match="Aardgas: Transporttarief"):
            client.get_data("85592NED", columns=["Transporttarief"])


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
