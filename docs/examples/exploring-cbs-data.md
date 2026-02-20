# Exploring CBS Data

CBS Statline hosts hundreds of publicly available datasets covering demographics, economics, health, and more. This guide shows how to discover and inspect datasets using cbspy.

## Listing available tables

Use `list_tables()` to get a DataFrame of all available CBS datasets. Pass `language="en"` to filter for English-language tables:

```python
import cbspy

client = cbspy.Client()

tables = client.list_tables(language="en")
print(f"Found {tables.shape[0]} English-language tables")
print(tables.head(5))
```

```
Found 1042 English-language tables
shape: (5, 7)
┌────────────┬──────────────────────────────────┬─────────────────┬──────────────┬───────────┬──────────────┬──────────────────────┐
│ id         ┆ title                            ┆ description     ┆ period       ┆ frequency ┆ record_count ┆ modified             │
│ ---        ┆ ---                              ┆ ---             ┆ ---          ┆ ---       ┆ ---          ┆ ---                  │
│ str        ┆ str                              ┆ str             ┆ str          ┆ str       ┆ i64          ┆ str                  │
╞════════════╪══════════════════════════════════╪═════════════════╪══════════════╪═══════════╪══════════════╪══════════════════════╡
│ 37296eng   ┆ Population; key figures          ┆ Population s... ┆ 1950 - 2023  ┆ Per year  ┆ 75           ┆ 2024-03-28T02:00:00  │
│ 37556eng   ┆ Births; key figures              ┆ Live born ch... ┆ 1950 - 2023  ┆ Per year  ┆ 74           ┆ 2024-06-28T02:00:00  │
│ 37583eng   ┆ Mortality; key figures           ┆ Number of de... ┆ 1950 - 2023  ┆ Per year  ┆ 74           ┆ 2024-06-28T02:00:00  │
│ 37679eng   ┆ Immigration and emigration ...   ┆ Immigrants a... ┆ 1995 - 2023  ┆ Per year  ┆ 29           ┆ 2024-08-02T02:00:00  │
│ 37943eng   ┆ Households; composition, size... ┆ Households b... ┆ 1995 - 2024  ┆ Per year  ┆ 30           ┆ 2024-10-18T02:00:00  │
└────────────┴──────────────────────────────────┴─────────────────┴──────────────┴───────────┴──────────────┴──────────────────────┘
```

You can also list Dutch-language tables by passing `language="nl"`, or get all tables by omitting the parameter.

## Searching for a topic

The returned DataFrame is a standard Polars DataFrame, so you can filter it with any Polars operation:

```python
# Find tables related to housing
housing = tables.filter(
    tables["title"].str.contains("(?i)housing|dwelling")
)
print(housing.select("id", "title"))
```

```
shape: (12, 2)
┌────────────┬──────────────────────────────────────────┐
│ id         ┆ title                                    │
│ ---        ┆ ---                                      │
│ str        ┆ str                                      │
╞════════════╪══════════════════════════════════════════╡
│ 82550ENG   ┆ Dwellings; main features                 │
│ 82900ENG   ┆ Existing dwellings; purchase prices ...  │
│ ...        ┆ ...                                      │
└────────────┴──────────────────────────────────────────┘
```

## Inspecting a table's columns

Once you've found a table, use `get_metadata()` to inspect its structure:

```python
meta = client.get_metadata("37296eng")
print(f"Table: {meta.title}")
print(f"Description: {meta.description}")
print(f"Period: {meta.period}")
print(f"Frequency: {meta.frequency}")
print(f"Columns: {len(meta.properties)}")
```

```
Table: Population; key figures
Description: Population size, growth and structure.
Period: 1950 - 2023
Frequency: Per year
Columns: 28
```

List the available columns:

```python
for col in meta.properties[:10]:
    unit = f" ({col.unit})" if col.unit else ""
    print(f"  {col.display_name}{unit}")
```

```
  Periods
  Total population (number)
  Population growth (number)
  Live born children (number)
  Deaths (number)
  Surplus births over deaths (number)
  Immigration (number)
  Emigration (number)
  Other corrections (number)
  Net migration including corrections (number)
```

## Fetching a data preview

Fetch a few rows to see what the data looks like:

```python
df = client.get_data("37296eng", periods=["2023JJ00"])
print(df)
```

```
shape: (1, 28)
┌─────────┬──────────────────┬───────────────────┬───────────────────┬───┐
│ Periods ┆ Total population ┆ Population growth ┆ Live born children┆ … │
│ ---     ┆ ---              ┆ ---               ┆ ---               ┆   │
│ str     ┆ i64              ┆ i64               ┆ i64               ┆   │
╞═════════╪══════════════════╪═══════════════════╪═══════════════════╪═══╡
│ 2023    ┆ 17811291         ┆ 220619            ┆ 168930            ┆ … │
└─────────┴──────────────────┴───────────────────┴───────────────────┴───┘
```

Notice that:

- The column `TotalPopulation_1` is displayed as `Total population`
- The period code `2023JJ00` is decoded to `2023`
- The internal `ID` column is removed automatically
