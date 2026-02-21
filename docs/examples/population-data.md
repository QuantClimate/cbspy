# Working with Population Data

This example uses the CBS population dataset (`37296eng`) to demonstrate cbspy's core features: fetching data, period filtering, and working with the resulting Polars DataFrame.

## Fetching population data

```python
import cbspy

client = cbspy.Client()

# Fetch the last 5 years of population data
df = client.get_data(
    "37296eng",
    periods=["2019JJ00", "2020JJ00", "2021JJ00", "2022JJ00", "2023JJ00"],
)
print(df.select("Periods", "Total population", "Population growth"))
```

```
shape: (5, 3)
┌─────────┬──────────────────┬───────────────────┐
│ Periods ┆ Total population ┆ Population growth │
│ ---     ┆ ---              ┆ ---               │
│ str     ┆ i64              ┆ i64               │
╞═════════╪══════════════════╪═══════════════════╡
│ 2019    ┆ 17282163         ┆ 132950            │
│ 2020    ┆ 17407585         ┆ 125422            │
│ 2021    ┆ 17475415         ┆ 67830             │
│ 2022    ┆ 17590672         ┆ 115257            │
│ 2023    ┆ 17811291         ┆ 220619            │
└─────────┴──────────────────┴───────────────────┘
```

## Selecting columns

The DataFrame has 28 columns. Use standard Polars operations to select what you need:

```python
demographics = df.select(
    "Periods",
    "Total population",
    "Males",
    "Females",
    "Live born children",
    "Deaths",
)
print(demographics)
```

```
shape: (5, 6)
┌─────────┬──────────────────┬─────────┬─────────┬────────────────────┬────────┐
│ Periods ┆ Total population ┆ Males   ┆ Females ┆ Live born children ┆ Deaths │
│ ---     ┆ ---              ┆ ---     ┆ ---     ┆ ---                ┆ ---    │
│ str     ┆ i64              ┆ i64     ┆ i64     ┆ i64                ┆ i64    │
╞═════════╪══════════════════╪═════════╪═════════╪════════════════════╪════════╡
│ 2019    ┆ 17282163         ┆ 8597810 ┆ 8684353 ┆ 169680             ┆ 151885 │
│ 2020    ┆ 17407585         ┆ 8656417 ┆ 8751168 ┆ 168678             ┆ 168566 │
│ 2021    ┆ 17475415         ┆ 8689075 ┆ 8786340 ┆ 179068             ┆ 170972 │
│ 2022    ┆ 17590672         ┆ 8758927 ┆ 8831745 ┆ 168903             ┆ 170112 │
│ 2023    ┆ 17811291         ┆ 8873596 ┆ 8937695 ┆ 168930             ┆ 169363 │
└─────────┴──────────────────┴─────────┴─────────┴────────────────────┴────────┘
```

## Computing derived values

Since the result is a Polars DataFrame, you can use all of Polars' expression API:

```python
import polars as pl

growth = df.select(
    "Periods",
    "Total population",
    pl.col("Population growth")
      .truediv(pl.col("Total population"))
      .mul(100)
      .round(2)
      .alias("Growth rate (%)"),
)
print(growth)
```

```
shape: (5, 3)
┌─────────┬──────────────────┬─────────────────┐
│ Periods ┆ Total population ┆ Growth rate (%) │
│ ---     ┆ ---              ┆ ---             │
│ str     ┆ i64              ┆ f64             │
╞═════════╪══════════════════╪═════════════════╡
│ 2019    ┆ 17282163         ┆ 0.77            │
│ 2020    ┆ 17407585         ┆ 0.72            │
│ 2021    ┆ 17475415         ┆ 0.39            │
│ 2022    ┆ 17590672         ┆ 0.66            │
│ 2023    ┆ 17811291         ┆ 1.24            │
└─────────┴──────────────────┴─────────────────┘
```

## Using period codes

CBS uses specific period code formats. Pass them directly to `periods`:

| Format | Example | Meaning |
|--------|---------|---------|
| Yearly | `2023JJ00` | Year 2023 |
| Half-yearly | `2023HJ01` | 2023 H1 |
| Quarterly | `2023KW01` | 2023 Q1 |
| Monthly | `2023MM03` | 2023 March |

cbspy automatically decodes these to human-readable labels in the output DataFrame.

```python
# Fetch a single year
df = client.get_data("37296eng", periods=["2023JJ00"])

# The Periods column shows "2023", not "2023JJ00"
print(df["Periods"].to_list())
```

```
['2023']
```

## Fetching all available data

Omit the `periods` parameter to fetch everything:

```python
df = client.get_data("37296eng")
print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
print(f"Years covered: {df['Periods'].head(1).item()} to {df['Periods'].tail(1).item()}")
```

```
Rows: 75, Columns: 28
Years covered: 1950 to 2023
```

!!! note
    Large datasets may take a moment to fetch. cbspy automatically handles pagination for datasets that exceed the CBS API's page size limit.
