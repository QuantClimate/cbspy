# Getting Started

## Installation

Install cbspy with pip:

```bash
pip install cbspy
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add cbspy
```

cbspy requires Python 3.10 or later.

## Discovering tables

CBS Statline hosts hundreds of datasets. Use `list_tables()` to browse them:

```python
import cbspy

client = cbspy.Client()

# List all English-language tables
tables = client.list_tables(language="en")
print(tables.head(5))
```

```
shape: (5, 7)
┌────────────┬──────────────────────┬─────────────┬─────────┬───────────┬──────────────┬──────────┐
│ id         ┆ title                ┆ description ┆ period  ┆ frequency ┆ record_count ┆ modified │
│ ---        ┆ ---                  ┆ ---         ┆ ---     ┆ ---       ┆ ---          ┆ ---      │
│ str        ┆ str                  ┆ str         ┆ str     ┆ str       ┆ i64          ┆ str      │
╞════════════╪══════════════════════╪═════════════╪═════════╪═══════════╪══════════════╪══════════╡
│ 37296eng   ┆ Population; key ...  ┆ ...         ┆ 1950-...┆ Per year  ┆ 75           ┆ 2024-... │
│ ...        ┆ ...                  ┆ ...         ┆ ...     ┆ ...       ┆ ...          ┆ ...      │
└────────────┴──────────────────────┴─────────────┴─────────┴───────────┴──────────────┴──────────┘
```

The returned DataFrame includes each table's ID, title, description, time period, update frequency, row count, and last modified date.

## Inspecting table metadata

Once you have a table ID, inspect its columns with `get_metadata()`:

```python
meta = client.get_metadata("37296eng")

print(f"Table: {meta.title}")
print(f"Period: {meta.period}")
print()

for col in meta.properties:
    print(f"  {col.display_name} ({col.unit})")
```

```
Table: Population; key figures
Period: 1950 - 2023

  Periods ()
  Total population (number)
  Population growth (number)
  Live born children (number)
  ...
```

Each `Column` object has `id`, `name`, `dutch_name`, `unit`, `datatype`, `description`, and a `display_name` computed property that prefers the English name.

## Fetching data

Fetch a dataset with `get_data()`. Column names are automatically resolved to human-readable labels:

```python
df = client.get_data("37296eng", periods=["2022JJ00", "2023JJ00"])
print(df)
```

```
shape: (2, 28)
┌─────────┬──────────────────┬───────────────────┬───────────┬───┐
│ Periods ┆ Total population ┆ Population growth ┆ Males     ┆ … │
│ ---     ┆ ---              ┆ ---               ┆ ---       ┆   │
│ str     ┆ i64              ┆ i64               ┆ i64       ┆   │
╞═════════╪══════════════════╪═══════════════════╪═══════════╪═══╡
│ 2022    ┆ 17590672         ┆ 227365            ┆ 8758927   ┆ … │
│ 2023    ┆ 17811291         ┆ 220619            ┆ 8873596   ┆ … │
└─────────┴──────────────────┴───────────────────┴───────────┴───┘
```

Period codes like `2022JJ00` are automatically decoded to `2022`. Quarterly periods (`2023KW01`) become `2023 Q1`, and monthly periods (`2023MM03`) become `2023 March`.

## Error handling

cbspy raises specific exceptions for common problems:

```python
from cbspy import TableNotFoundError, APIError

try:
    client.get_data("nonexistent_table")
except TableNotFoundError:
    print("Table does not exist. Use list_tables() to find valid IDs.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

All exceptions inherit from `CBSError`, so you can catch everything with a single handler if preferred.

## Next steps

- Browse the [API Reference](api-reference.md) for full method signatures
- Try the [Interactive Examples](examples/exploring-cbs-data.md) to explore CBS data
