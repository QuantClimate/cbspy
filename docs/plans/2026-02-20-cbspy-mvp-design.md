# cbspy MVP Design

A modern Python client for CBS Statline open data, targeted at developers who want Dutch statistical data but are not fluent in Dutch.

## Context

CBS Statline (opendata.cbs.nl) exposes Dutch government statistics via an OData v3 API. An existing library, `cbsodata`, wraps this API but was last updated in 2021 and lacks modern Python conveniences. CBS plans to migrate from OData to SDMX (postponed to 2026+), so the OData API remains the current interface.

## Architecture: Thin OData Client

A focused wrapper around the CBS OData v3 API with Polars output.

The client maps directly to CBS API operations. No domain-specific facades, no query builder abstractions. Users interact with CBS table identifiers and get back clean, well-typed DataFrames.

## Public API

```python
import cbspy

client = cbspy.Client()

# Discover tables
tables = client.list_tables(language="en")
# -> Polars DataFrame: id, title, description, period, frequency, record_count, modified

# Inspect a table's structure
meta = client.get_metadata("37296eng")
# -> TableMetadata with properties: list[Column]

# Fetch data
df = client.get_data("37296eng")
# -> Polars DataFrame with human-readable column names

# Filter at the OData level
df = client.get_data("37296eng", periods=["2022JJ00", "2023JJ00"])
```

Everything goes through the `Client` instance. No global state, no module-level functions. Users can configure the base URL or pass a custom httpx client for testing.

## Data Models (Pydantic)

```python
class Column(BaseModel):
    id: str              # "TotaleBevolking_1"
    name: str            # "Total population" (English or Dutch)
    dutch_name: str      # "Totale bevolking"
    unit: str            # "" or "x 1 000" or "%"
    type: str            # "Double", "Long", "TimeDimension"
    description: str     # Extended description

class TableMetadata(BaseModel):
    id: str
    title: str
    description: str
    period: str           # "1950 - 2022"
    frequency: str
    properties: list[Column]
```

## Column Resolution

When `get_data()` is called:

1. Fetch `DataProperties` for the table (column schema with IDs, titles, units, types)
2. Fetch `TypedDataSet` (raw data with cryptic column IDs like `TotaleBevolking_1`)
3. Map column IDs to English titles using the properties
4. Decode CBS period codes (`2023JJ00` -> yearly, `2023KW01` -> Q1, `2023MM03` -> March)
5. Build Polars DataFrame with clean column names and proper dtypes

Bilingual approach: expose both Dutch and English names in Column metadata. When a table only has Dutch names, `Column.name` falls back to `Column.dutch_name`.

## Project Structure

```
src/cbspy/
    __init__.py          # Re-exports Client, TableMetadata, Column
    client.py            # Client class with list_tables, get_metadata, get_data
    models.py            # Pydantic models: Column, TableMetadata
    _odata.py            # Low-level OData HTTP calls (internal)
    _periods.py          # Period string decoder (internal)
```

Internal modules prefixed with `_`. Users only interact with the public API.

## Dependencies

**Runtime:**
- `httpx` — HTTP client (sync)
- `polars` — DataFrame output
- `pydantic` — data models

**Dev (already configured):**
- pytest, ruff, ty, mkdocs, pre-commit, tox-uv
- `respx` — httpx mocking (to add)

## Error Handling

```python
class CBSError(Exception):
    """Base exception for cbspy."""

class TableNotFoundError(CBSError):
    """Raised when a table ID doesn't exist."""

class APIError(CBSError):
    """Raised when CBS API returns an error response."""
    status_code: int
    message: str
```

Edge cases:
- **Table not found:** Raise `TableNotFoundError` with helpful message suggesting `list_tables()`
- **Rate limiting / 5xx:** Retry once with backoff, then raise `APIError`
- **Empty datasets:** Return empty DataFrame, don't raise
- **Large datasets:** Follow OData `odata.nextLink` pagination automatically
- **Missing English metadata:** Fall back to Dutch names (`Column.name = Column.dutch_name`)

## Testing

```
tests/
    conftest.py          # Shared fixtures (mock client, sample responses)
    fixtures/            # Sample CBS API response JSON files
    test_client.py       # Client method tests
    test_models.py       # Pydantic model validation tests
    test_odata.py        # Low-level OData HTTP tests
    test_periods.py      # Period decoder unit tests
```

- Unit tests with `respx` mocks — no real network calls
- Fixture JSON captured from real CBS API responses
- `@pytest.mark.integration` for optional real API tests (skipped by default)
- Period decoder: comprehensive coverage of all CBS formats (JJ, KW, MM)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Thin OData client | Fastest to ship, layer more on top later |
| Output | Polars | Modern, fast, great type support |
| Models | Pydantic | Validation, serialization, IDE support |
| HTTP | httpx (sync) | Modern, easy async upgrade path |
| Translation | Bilingual labels | Expose both Dutch and English names |
| Testing | respx mocks | Ergonomic httpx mocking |

## Future Considerations (Not MVP)

- Async support via httpx async client
- Domain-specific convenience methods (population, economy)
- Query builder pattern for complex OData filters
- SDMX support when CBS completes migration
- Caching layer for frequently accessed tables
