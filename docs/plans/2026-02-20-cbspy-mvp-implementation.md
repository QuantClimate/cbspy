# cbspy MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a modern Python client for CBS Statline open data that returns Polars DataFrames with human-readable column names.

**Architecture:** Thin OData v3 client. A `Client` class wraps httpx, calls the CBS OData API, resolves cryptic column IDs to English names via `DataProperties`, and returns Polars DataFrames. Pydantic models for metadata. Internal modules for HTTP and period decoding.

**Tech Stack:** Python 3.10+, httpx, polars, pydantic, respx (dev), pytest, ruff, uv

---

### Task 1: Project Scaffolding — Add Dependencies and Clean Placeholder Code

**Files:**
- Modify: `pyproject.toml`
- Delete: `src/cbspy/foo.py`
- Delete: `tests/test_foo.py`
- Modify: `src/cbspy/__init__.py`

**Step 1: Add runtime dependencies to pyproject.toml**

In `pyproject.toml`, add a `dependencies` list under `[project]` (after `requires-python`):

```toml
dependencies = [
    "httpx>=0.27",
    "polars>=1.0",
    "pydantic>=2.0",
]
```

And add `respx` to the dev dependency group:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pre-commit>=4.5.1",
    "tox-uv>=1.29.0",
    "ty>=0.0.14",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.14",
    "mkdocs>=1.6.1",
    "mkdocs-material>=9.7.1",
    "mkdocstrings[python]>=1.0.2",
    "respx>=0.22",
]
```

**Step 2: Delete placeholder files**

```bash
rm src/cbspy/foo.py tests/test_foo.py
```

**Step 3: Clear `src/cbspy/__init__.py`**

Make it an empty file for now. We'll add re-exports later.

**Step 4: Install dependencies**

```bash
uv sync
```

Verify httpx, polars, pydantic, respx are installed.

**Step 5: Run tests to confirm clean state**

```bash
uv run pytest -v
```

Expected: no tests collected, no errors.

**Step 6: Commit**

```bash
git add -A
git commit -m "chore: add runtime deps (httpx, polars, pydantic) and clean placeholders"
```

---

### Task 2: Pydantic Models — `Column`, `TableMetadata`, Exceptions

**Files:**
- Create: `src/cbspy/models.py`
- Create: `src/cbspy/exceptions.py`
- Create: `tests/test_models.py`

**Step 1: Write failing tests for models**

Create `tests/test_models.py`:

```python
from cbspy.models import Column, TableMetadata


def test_column_creation():
    col = Column(
        id="TotalPopulation_1",
        name="Total population",
        dutch_name="Totale bevolking",
        unit="number",
        datatype="Double",
        description="The total population.",
    )
    assert col.id == "TotalPopulation_1"
    assert col.name == "Total population"
    assert col.dutch_name == "Totale bevolking"
    assert col.unit == "number"
    assert col.datatype == "Double"
    assert col.description == "The total population."


def test_column_name_falls_back_to_dutch():
    col = Column(
        id="Foo_1",
        name="",
        dutch_name="Nederlandse naam",
        unit="",
        datatype="Long",
        description="",
    )
    assert col.display_name == "Nederlandse naam"


def test_column_name_prefers_english():
    col = Column(
        id="Foo_1",
        name="English name",
        dutch_name="Nederlandse naam",
        unit="",
        datatype="Long",
        description="",
    )
    assert col.display_name == "English name"


def test_table_metadata_creation():
    meta = TableMetadata(
        id="37296eng",
        title="Population; key figures",
        description="A description.",
        period="1950 - 2022",
        frequency="Perjaar",
        properties=[],
    )
    assert meta.id == "37296eng"
    assert meta.title == "Population; key figures"
    assert meta.properties == []


def test_table_metadata_with_columns():
    col = Column(
        id="TotalPopulation_1",
        name="Total population",
        dutch_name="Totale bevolking",
        unit="number",
        datatype="Double",
        description="",
    )
    meta = TableMetadata(
        id="37296eng",
        title="Population; key figures",
        description="",
        period="1950 - 2022",
        frequency="Perjaar",
        properties=[col],
    )
    assert len(meta.properties) == 1
    assert meta.properties[0].id == "TotalPopulation_1"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'cbspy.models'`

**Step 3: Write the models**

Create `src/cbspy/models.py`:

```python
from pydantic import BaseModel, computed_field


class Column(BaseModel):
    """A column (property) in a CBS dataset."""

    id: str
    name: str
    dutch_name: str
    unit: str
    datatype: str
    description: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        """Return English name if available, otherwise Dutch."""
        return self.name if self.name else self.dutch_name


class TableMetadata(BaseModel):
    """Metadata for a CBS dataset table."""

    id: str
    title: str
    description: str
    period: str
    frequency: str
    properties: list[Column]
```

**Step 4: Write exceptions**

Create `src/cbspy/exceptions.py`:

```python
class CBSError(Exception):
    """Base exception for cbspy."""


class TableNotFoundError(CBSError):
    """Raised when a CBS table ID does not exist.

    Use client.list_tables() to discover available tables.
    """


class APIError(CBSError):
    """Raised when the CBS API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"CBS API error {status_code}: {message}")
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all 5 tests pass.

**Step 6: Commit**

```bash
git add src/cbspy/models.py src/cbspy/exceptions.py tests/test_models.py
git commit -m "feat: add Pydantic models (Column, TableMetadata) and exceptions"
```

---

### Task 3: Period Decoder — `_periods.py`

CBS encodes time periods as strings. This module decodes them to human-readable labels.

Formats:
- `2023JJ00` → `"2023"` (yearly)
- `2023KW01` → `"2023 Q1"` (quarterly)
- `2023MM03` → `"2023 March"` (monthly)

**Files:**
- Create: `src/cbspy/_periods.py`
- Create: `tests/test_periods.py`

**Step 1: Write failing tests**

Create `tests/test_periods.py`:

```python
import pytest

from cbspy._periods import decode_period


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2023JJ00", "2023"),
        ("1950JJ00", "1950"),
        ("2023KW01", "2023 Q1"),
        ("2023KW02", "2023 Q2"),
        ("2023KW03", "2023 Q3"),
        ("2023KW04", "2023 Q4"),
        ("2023MM01", "2023 January"),
        ("2023MM06", "2023 June"),
        ("2023MM12", "2023 December"),
    ],
)
def test_decode_period(raw: str, expected: str):
    assert decode_period(raw) == expected


def test_decode_period_unknown_format():
    assert decode_period("UNKNOWN") == "UNKNOWN"


def test_decode_period_strips_whitespace():
    assert decode_period("  2023JJ00  ") == "2023"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_periods.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Implement the decoder**

Create `src/cbspy/_periods.py`:

```python
import re

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_YEARLY = re.compile(r"^(\d{4})JJ00$")
_QUARTERLY = re.compile(r"^(\d{4})KW0([1-4])$")
_MONTHLY = re.compile(r"^(\d{4})MM(\d{2})$")


def decode_period(raw: str) -> str:
    """Decode a CBS period code to a human-readable label.

    Examples:
        2023JJ00 -> "2023"
        2023KW01 -> "2023 Q1"
        2023MM03 -> "2023 March"
    """
    s = raw.strip()

    if m := _YEARLY.match(s):
        return m.group(1)

    if m := _QUARTERLY.match(s):
        return f"{m.group(1)} Q{m.group(2)}"

    if m := _MONTHLY.match(s):
        month_idx = int(m.group(2))
        if 1 <= month_idx <= 12:
            return f"{m.group(1)} {_MONTHS[month_idx - 1]}"

    return s
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_periods.py -v
```

Expected: all 12 tests pass.

**Step 5: Commit**

```bash
git add src/cbspy/_periods.py tests/test_periods.py
git commit -m "feat: add CBS period code decoder"
```

---

### Task 4: OData HTTP Layer — `_odata.py`

Low-level module that handles all HTTP communication with the CBS API. Responsible for URL construction, pagination, error mapping, and returning raw Python dicts.

**Files:**
- Create: `src/cbspy/_odata.py`
- Create: `tests/test_odata.py`
- Create: `tests/conftest.py`

**Step 1: Write failing tests**

Create `tests/conftest.py`:

```python
import pytest
import httpx


@pytest.fixture
def http_client():
    """A real httpx client for building OData instances in tests."""
    return httpx.Client()
```

Create `tests/test_odata.py`:

```python
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
            return_value=httpx.Response(200, json={
                "value": [{"ID": 0, "Periods": "2023JJ00"}]
            })
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0, "Periods": "2023JJ00"}]

    @respx.mock
    def test_follows_pagination(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={
                "value": [{"ID": 0}],
                "odata.nextLink": f"{BASE}/ODataApi/odata/37296eng/TypedDataSet?$skip=1",
            })
        )
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet", params={"$skip": "1"}).mock(
            return_value=httpx.Response(200, json={
                "value": [{"ID": 1}],
            })
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_json("37296eng", "TypedDataSet")
        assert result == [{"ID": 0}, {"ID": 1}]

    @respx.mock
    def test_404_raises_table_not_found(self):
        respx.get(f"{BASE}/ODataApi/odata/FAKE/TypedDataSet").mock(
            return_value=httpx.Response(404, text="Not found")
        )
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
            return_value=httpx.Response(200, json={
                "value": [{"Identifier": "37296eng", "Title": "Population"}]
            })
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_catalog()
        assert result == [{"Identifier": "37296eng", "Title": "Population"}]

    @respx.mock
    def test_catalog_with_language_filter(self):
        respx.get(f"{BASE}/ODataCatalog/Tables").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"Identifier": "37296eng", "Title": "Population", "Language": "en"},
                    {"Identifier": "37296", "Title": "Bevolking", "Language": "nl"},
                ]
            })
        )
        client = ODataClient(base_url=BASE, http_client=httpx.Client())
        result = client.get_catalog(language="en")
        assert len(result) == 1
        assert result[0]["Language"] == "en"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_odata.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Implement `_odata.py`**

Create `src/cbspy/_odata.py`:

```python
from __future__ import annotations

from typing import Any

import httpx

from cbspy.exceptions import APIError, TableNotFoundError

_ODATA_API = "/ODataApi/odata"
_CATALOG = "/ODataCatalog/Tables"


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
            response = self._http.get(url, params=request_params)
            self._check_response(response, table_id)

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
            response = self._http.get(url, params=params)
            self._check_response(response, "catalog")

            body = response.json()
            all_rows.extend(body.get("value", []))

            url = body.get("odata.nextLink")
            params = {}

        return all_rows

    def _check_response(self, response: httpx.Response, table_id: str) -> None:
        """Raise appropriate exception for error responses."""
        if response.status_code == 404:
            msg = f"Table '{table_id}' not found. Use client.list_tables() to discover available tables."
            raise TableNotFoundError(msg)
        if response.status_code >= 400:
            raise APIError(status_code=response.status_code, message=response.text)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_odata.py -v
```

Expected: all 6 tests pass.

**Step 5: Commit**

```bash
git add src/cbspy/_odata.py src/cbspy/exceptions.py tests/test_odata.py tests/conftest.py
git commit -m "feat: add OData HTTP layer with pagination and error handling"
```

---

### Task 5: Client — `list_tables()` and `get_metadata()`

The public-facing `Client` class. This task implements discovery and metadata inspection.

**Files:**
- Create: `src/cbspy/client.py`
- Create: `tests/test_client.py`

**Step 1: Write failing tests**

Create `tests/test_client.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_client.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Implement `client.py`**

Create `src/cbspy/client.py`:

```python
from __future__ import annotations

from typing import Any

import httpx
import polars as pl

from cbspy._odata import ODataClient
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
        self._http = http_client or httpx.Client()
        self._odata = ODataClient(base_url=base_url, http_client=self._http)

    def list_tables(self, language: str | None = None) -> pl.DataFrame:
        """List available CBS tables.

        Args:
            language: Filter by language ("en" or "nl"). Returns all if None.

        Returns:
            Polars DataFrame with columns: id, title, description, period,
            frequency, record_count, modified.
        """
        rows = self._odata.get_catalog(language=language)
        return pl.DataFrame(
            {
                "id": [r["Identifier"] for r in rows],
                "title": [r["Title"] for r in rows],
                "description": [r.get("ShortDescription", "") for r in rows],
                "period": [r.get("Period", "") for r in rows],
                "frequency": [r.get("Frequency", "") for r in rows],
                "record_count": [r.get("RecordCount", 0) for r in rows],
                "modified": [r.get("Modified", "") for r in rows],
            }
        )

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

    @staticmethod
    def _parse_column(prop: dict[str, Any]) -> Column:
        """Convert a raw DataProperties entry to a Column model."""
        return Column(
            id=prop.get("Key", ""),
            name=prop.get("Title", ""),
            dutch_name=prop.get("Title", ""),
            unit=prop.get("Unit", ""),
            datatype=prop.get("Datatype", prop.get("Type", "")),
            description=prop.get("Description", ""),
        )
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_client.py -v
```

Expected: all 4 tests pass.

**Step 5: Commit**

```bash
git add src/cbspy/client.py tests/test_client.py
git commit -m "feat: add Client with list_tables() and get_metadata()"
```

---

### Task 6: Client — `get_data()`

The main data-fetching method. Fetches `TypedDataSet`, resolves column names via `DataProperties`, decodes period codes, and returns a Polars DataFrame.

**Files:**
- Modify: `src/cbspy/client.py`
- Modify: `tests/test_client.py`

**Step 1: Write failing tests**

Add to `tests/test_client.py`:

```python
class TestGetData:
    @respx.mock
    def test_returns_dataframe_with_resolved_columns(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/DataProperties").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"odata.type": "Cbs.OData.TimeDimension", "ID": 0, "Key": "Periods",
                     "Title": "Periods", "Description": "", "Type": "TimeDimension"},
                    {"odata.type": "Cbs.OData.Topic", "ID": 1, "Key": "TotalPopulation_1",
                     "Title": "Total population", "Description": "", "Type": "Topic",
                     "Datatype": "Double", "Unit": "number"},
                    {"odata.type": "Cbs.OData.Topic", "ID": 2, "Key": "Males_2",
                     "Title": "Males", "Description": "", "Type": "Topic",
                     "Datatype": "Long", "Unit": "number"},
                ]
            })
        )
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291, "Males_2": 8864},
                    {"ID": 1, "Periods": "2022JJ00", "TotalPopulation_1": 17590672, "Males_2": 8757},
                ]
            })
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
        respx.get(f"{BASE}/ODataApi/odata/37296eng/DataProperties").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"odata.type": "Cbs.OData.TimeDimension", "ID": 0, "Key": "Periods",
                     "Title": "Periods", "Description": "", "Type": "TimeDimension"},
                    {"odata.type": "Cbs.OData.Topic", "ID": 1, "Key": "TotalPopulation_1",
                     "Title": "Total population", "Description": "", "Type": "Topic",
                     "Datatype": "Double", "Unit": "number"},
                ]
            })
        )
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"ID": 0, "Periods": "2023JJ00", "TotalPopulation_1": 17811291},
                ]
            })
        )
        client = Client()
        df = client.get_data("37296eng", periods=["2023JJ00"])
        assert df.shape[0] == 1

    @respx.mock
    def test_get_data_empty_dataset(self):
        respx.get(f"{BASE}/ODataApi/odata/37296eng/DataProperties").mock(
            return_value=httpx.Response(200, json={
                "value": [
                    {"odata.type": "Cbs.OData.TimeDimension", "ID": 0, "Key": "Periods",
                     "Title": "Periods", "Description": "", "Type": "TimeDimension"},
                ]
            })
        )
        respx.get(f"{BASE}/ODataApi/odata/37296eng/TypedDataSet").mock(
            return_value=httpx.Response(200, json={"value": []})
        )
        client = Client()
        df = client.get_data("37296eng")
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 0
```

**Step 2: Run tests to verify the new ones fail**

```bash
uv run pytest tests/test_client.py::TestGetData -v
```

Expected: `AttributeError: 'Client' object has no attribute 'get_data'`

**Step 3: Implement `get_data()` in `client.py`**

Add these imports to the top of `src/cbspy/client.py`:

```python
from cbspy._periods import decode_period
```

Add to the `Client` class:

```python
    def get_data(self, table_id: str, periods: list[str] | None = None) -> pl.DataFrame:
        """Fetch dataset as a Polars DataFrame with human-readable column names.

        Args:
            table_id: CBS table identifier (e.g. "37296eng").
            periods: Optional list of CBS period codes to filter by.

        Returns:
            Polars DataFrame with resolved column names and decoded periods.
        """
        prop_rows = self._odata.get_json(table_id, "DataProperties")
        column_map = {p["Key"]: p.get("Title", p["Key"]) for p in prop_rows}
        period_keys = {p["Key"] for p in prop_rows if p.get("Type") == "TimeDimension"}

        params: dict[str, str] | None = None
        if periods:
            period_filter = " or ".join(f"Periods eq '{p}'" for p in periods)
            params = {"$filter": period_filter}

        data_rows = self._odata.get_json(table_id, "TypedDataSet", params=params)

        if not data_rows:
            columns = {column_map.get(k, k): [] for k in column_map}
            return pl.DataFrame(columns)

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
```

**Step 4: Run all tests**

```bash
uv run pytest tests/test_client.py -v
```

Expected: all 7 tests pass.

**Step 5: Commit**

```bash
git add src/cbspy/client.py tests/test_client.py
git commit -m "feat: add Client.get_data() with column resolution and period decoding"
```

---

### Task 7: Public API — Wire Up `__init__.py`

**Files:**
- Modify: `src/cbspy/__init__.py`

**Step 1: Write a failing test for public imports**

Add to `tests/test_client.py` (top-level, outside any class):

```python
def test_public_imports():
    from cbspy import Client, Column, TableMetadata, CBSError, TableNotFoundError, APIError

    assert Client is not None
    assert Column is not None
    assert TableMetadata is not None
    assert CBSError is not None
    assert TableNotFoundError is not None
    assert APIError is not None
```

**Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_client.py::test_public_imports -v
```

Expected: `ImportError: cannot import name 'Client' from 'cbspy'`

**Step 3: Update `__init__.py`**

Write `src/cbspy/__init__.py`:

```python
from cbspy.client import Client
from cbspy.exceptions import APIError, CBSError, TableNotFoundError
from cbspy.models import Column, TableMetadata

__all__ = [
    "Client",
    "Column",
    "TableMetadata",
    "CBSError",
    "TableNotFoundError",
    "APIError",
]
```

**Step 4: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/cbspy/__init__.py tests/test_client.py
git commit -m "feat: wire up public API exports"
```

---

### Task 8: Linting, Type Checking, and Final Polish

**Files:**
- Possibly modify any file that has lint issues

**Step 1: Run ruff**

```bash
uv run ruff check src/ tests/
```

Fix any issues reported.

**Step 2: Run ruff format**

```bash
uv run ruff format src/ tests/
```

**Step 3: Run type checker**

```bash
uv run ty check
```

Fix any type errors reported.

**Step 4: Run full test suite with coverage**

```bash
uv run pytest --cov --cov-config=pyproject.toml --cov-report=term-missing
```

Expected: all tests pass, reasonable coverage (>80%).

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint and type errors"
```

---

### Task 9: Update README

**Files:**
- Modify: `README.md`

**Step 1: Replace the cookiecutter README with library documentation**

Replace `README.md` with content covering:

- What cbspy is (one sentence)
- Installation: `pip install cbspy`
- Quick start example showing `list_tables()`, `get_metadata()`, `get_data()`
- Link to full docs
- Development setup (`make install`, `make test`, `make check`)

Use the examples from the design doc as the basis.

**Step 2: Verify docs build**

```bash
uv run mkdocs build -s
```

Fix any warnings.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with library usage examples"
```

---

## Task Dependency Graph

```
Task 1 (scaffolding)
  ├── Task 2 (models + exceptions)
  │     └── Task 4 (OData HTTP layer)
  │           └── Task 5 (Client: list_tables, get_metadata)
  │                 └── Task 6 (Client: get_data)
  │                       └── Task 7 (public API __init__.py)
  │                             └── Task 8 (lint + types)
  │                                   └── Task 9 (README)
  └── Task 3 (period decoder — independent)
```

Tasks 2 and 3 can be done in parallel after Task 1. Everything else is sequential.
