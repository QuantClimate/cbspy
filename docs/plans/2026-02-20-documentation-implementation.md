# cbspy Documentation Site Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive documentation site for cbspy with four sections: Home, Getting Started, API Reference, and Interactive Examples (3 pages).

**Architecture:** MkDocs + Material for MkDocs + mkdocs-marimo. Static pages use standard markdown with code fences and pre-rendered output. One interactive page (Period Codes) uses mkdocs-marimo's inline `{marimo}` blocks for in-browser interactivity via Pyodide/WASM. The other two example pages use static code + output since they require cbspy (not on PyPI) and httpx (not available in Pyodide).

**Tech Stack:** MkDocs, mkdocs-material, mkdocs-marimo, mkdocstrings[python], marimo, pymdownx extensions.

---

### Task 1: Add dependencies and update mkdocs.yml

**Files:**
- Modify: `pyproject.toml:31-43` (dev dependency group)
- Modify: `mkdocs.yml` (full rewrite of config)

**Step 1: Add marimo dependencies to pyproject.toml**

Add these two lines to the `[dependency-groups] dev` list in `pyproject.toml`:

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
    "mkdocs-marimo>=0.2",
    "marimo>=0.12",
]
```

**Step 2: Update mkdocs.yml**

Replace the entire `mkdocs.yml` with:

```yaml
site_name: cbspy
repo_url: https://github.com/thomaspinder/cbspy
site_url: https://thomaspinder.github.io/cbspy
site_description: A modern Python client for CBS Statline open data.
site_author: Thomas Pinder
edit_uri: edit/main/docs/
repo_name: thomaspinder/cbspy
copyright: Maintained by <a href="https://thomaspinder.com">thomaspinder</a>.

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api-reference.md
  - Interactive Examples:
    - Exploring CBS Data: examples/exploring-cbs-data.md
    - Working with Population Data: examples/population-data.md
    - Period Codes & Column Resolution: examples/period-codes.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: ["src/cbspy"]
  - marimo

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - content.code.copy
    - search.highlight
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: white
      accent: deep orange
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: black
      accent: deep orange
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  icon:
    repo: fontawesome/brands/github

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/thomaspinder/cbspy
    - icon: fontawesome/brands/python
      link: https://pypi.org/project/cbspy

markdown_extensions:
  - toc:
      permalink: true
  - admonition
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
```

**Step 3: Install dependencies**

Run: `uv sync`
Expected: Dependencies install without errors.

**Step 4: Verify MkDocs still builds**

Run: `uv run mkdocs build`
Expected: Build succeeds (may warn about missing nav pages -- that's fine for now).

**Step 5: Commit**

```bash
git add pyproject.toml mkdocs.yml
git commit -m "docs: add marimo dependencies and update mkdocs config"
```

---

### Task 2: Rewrite the Home page (index.md)

**Files:**
- Modify: `docs/index.md`

**Step 1: Write the home page**

Replace `docs/index.md` with:

```markdown
# cbspy

[![Release](https://img.shields.io/github/v/release/thomaspinder/cbspy)](https://img.shields.io/github/v/release/thomaspinder/cbspy)
[![Build status](https://img.shields.io/github/actions/workflow/status/thomaspinder/cbspy/main.yml?branch=main)](https://github.com/thomaspinder/cbspy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/thomaspinder/cbspy/branch/main/graph/badge.svg)](https://codecov.io/gh/thomaspinder/cbspy)
[![License](https://img.shields.io/github/license/thomaspinder/cbspy)](https://img.shields.io/github/license/thomaspinder/cbspy)

A modern Python client for [CBS Statline](https://opendata.cbs.nl) open data that returns [Polars](https://pola.rs) DataFrames with human-readable column names.

## Features

- Discover and search available CBS datasets
- Inspect table metadata and column definitions
- Fetch data as Polars DataFrames with resolved column names
- Automatic period code decoding (e.g. `2023KW01` becomes `2023 Q1`)
- Bilingual support (English and Dutch column names)

## Installation

```bash
pip install cbspy
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add cbspy
```

## Quick example

```python
import cbspy

client = cbspy.Client()

# Fetch population data with human-readable columns
df = client.get_data("37296eng", periods=["2023JJ00"])
print(df)
```

See the [Getting Started](getting-started.md) guide for a full walkthrough, or explore the [Interactive Examples](examples/exploring-cbs-data.md).
```

**Step 2: Verify the page builds**

Run: `uv run mkdocs build`
Expected: Build succeeds. Check `site/index.html` exists.

**Step 3: Commit**

```bash
git add docs/index.md
git commit -m "docs: rewrite home page with features and quick example"
```

---

### Task 3: Create the Getting Started page

**Files:**
- Create: `docs/getting-started.md`

**Step 1: Write the Getting Started page**

Create `docs/getting-started.md`:

```markdown
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
```

**Step 2: Verify the page builds**

Run: `uv run mkdocs build`
Expected: Build succeeds.

**Step 3: Commit**

```bash
git add docs/getting-started.md
git commit -m "docs: add Getting Started guide with examples"
```

---

### Task 4: Create the API Reference page

**Files:**
- Modify: `docs/modules.md` -> rename to `docs/api-reference.md`

**Step 1: Replace modules.md with api-reference.md**

Delete `docs/modules.md` and create `docs/api-reference.md`:

```markdown
# API Reference

## Client

::: cbspy.client.Client
    options:
      show_root_heading: true
      show_source: false
      members_order: source

## Data Models

### Column

::: cbspy.models.Column
    options:
      show_root_heading: true
      show_source: false

### TableMetadata

::: cbspy.models.TableMetadata
    options:
      show_root_heading: true
      show_source: false

## Exceptions

::: cbspy.exceptions.CBSError
    options:
      show_root_heading: true
      show_source: false

::: cbspy.exceptions.TableNotFoundError
    options:
      show_root_heading: true
      show_source: false

::: cbspy.exceptions.APIError
    options:
      show_root_heading: true
      show_source: false
```

**Step 2: Verify mkdocstrings renders correctly**

Run: `uv run mkdocs build`
Expected: Build succeeds. Check that `site/api-reference/index.html` exists and contains rendered docstrings.

**Step 3: Commit**

```bash
git rm docs/modules.md
git add docs/api-reference.md
git commit -m "docs: replace modules page with structured API Reference"
```

---

### Task 5: Create the examples directory and "Exploring CBS Data" page

**Files:**
- Create: `docs/examples/exploring-cbs-data.md`

**Step 1: Create the examples directory**

Run: `mkdir -p docs/examples`

**Step 2: Write the Exploring CBS Data page**

Create `docs/examples/exploring-cbs-data.md`:

```markdown
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
```

**Step 3: Verify the page builds**

Run: `uv run mkdocs build`
Expected: Build succeeds.

**Step 4: Commit**

```bash
git add docs/examples/exploring-cbs-data.md
git commit -m "docs: add Exploring CBS Data example page"
```

---

### Task 6: Create the "Working with Population Data" page

**Files:**
- Create: `docs/examples/population-data.md`

**Step 1: Write the Population Data page**

Create `docs/examples/population-data.md`:

```markdown
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
```

**Step 2: Verify the page builds**

Run: `uv run mkdocs build`
Expected: Build succeeds.

**Step 3: Commit**

```bash
git add docs/examples/population-data.md
git commit -m "docs: add Working with Population Data example page"
```

---

### Task 7: Create the interactive "Period Codes & Column Resolution" page

**Files:**
- Create: `docs/examples/period-codes.md`

This page uses mkdocs-marimo's `{marimo}` code fences for interactive elements. Since the period decoder uses only the `re` standard library module, it works in Pyodide/WASM without needing to import cbspy.

**Step 1: Write the Period Codes page**

Create `docs/examples/period-codes.md`:

````markdown
# Period Codes & Column Resolution

CBS Statline uses internal encodings for time periods and column names. cbspy automatically decodes these to human-readable labels. This page explains how the decoding works, with interactive examples you can try in your browser.

## Period code formats

CBS encodes time periods as strings with a specific format:

| Pattern | Example | Decoded |
|---------|---------|---------|
| `YYYYJJnn` | `2023JJ00` | `2023` (yearly) |
| `YYYYKWnn` | `2023KW01` | `2023 Q1` (quarterly) |
| `YYYYMMnn` | `2023MM03` | `2023 March` (monthly) |

## Try the period decoder

Type a CBS period code below to see how cbspy decodes it:

```python {marimo}
import marimo as mo
import re

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_YEARLY = re.compile(r"^(\d{4})JJ00$")
_QUARTERLY = re.compile(r"^(\d{4})KW0([1-4])$")
_MONTHLY = re.compile(r"^(\d{4})MM(\d{2})$")


def decode_period(raw: str) -> str:
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


period_input = mo.ui.text(value="2023KW01", label="Period code")
period_input
```

```python {marimo}
decoded = decode_period(period_input.value)
mo.md(f"**Input:** `{period_input.value}` **&rarr;** **Output:** `{decoded}`")
```

Try these examples:

- `2023JJ00` (yearly)
- `2023KW03` (quarterly -- Q3)
- `2023MM12` (monthly -- December)
- `1990JJ00` (older data)

## Batch decoding

Here is a batch of period codes and their decoded values:

```python {marimo}
examples = [
    "2023JJ00", "2022JJ00", "2021JJ00",
    "2023KW01", "2023KW02", "2023KW03", "2023KW04",
    "2023MM01", "2023MM06", "2023MM12",
    "unknown_format",
]
rows = [{"Period code": code, "Decoded": decode_period(code)} for code in examples]
mo.ui.table(rows, selection=None)
```

## How period decoding works

cbspy uses three regular expressions to match period codes:

1. **Yearly:** `^\d{4}JJ00$` -- matches codes like `2023JJ00`. Extracts the four-digit year.
2. **Quarterly:** `^\d{4}KW0[1-4]$` -- matches codes like `2023KW01`. Extracts year and quarter number.
3. **Monthly:** `^\d{4}MM\d{2}$` -- matches codes like `2023MM03`. Extracts year and month number, then maps to the month name.

If none of the patterns match, the original string is returned unchanged. This ensures that unexpected formats pass through without raising errors.

## Column resolution

When you call `client.get_data()`, cbspy renames columns from CBS internal IDs to human-readable titles. For example:

| CBS internal ID | Resolved column name |
|-----------------|---------------------|
| `TotalPopulation_1` | Total population |
| `Males_2` | Males |
| `Females_3` | Females |
| `LiveBornChildren_4` | Live born children |
| `Periods` | Periods |

This mapping is built from the table's `DataProperties` resource, which contains a `Key` (internal ID) and `Title` (display name) for each column.

### The resolution flow

1. cbspy fetches `DataProperties` for the requested table
2. Builds a mapping: `{Key: Title}` for each column
3. Identifies period columns (those with `Type == "TimeDimension"`)
4. Fetches the raw data from `TypedDataSet`
5. Renames each column using the mapping
6. Decodes period values in period columns
7. Removes the internal `ID` column
8. Returns a Polars DataFrame with clean column names
````

**Step 2: Verify the page builds**

Run: `uv run mkdocs build`
Expected: Build succeeds. The `{marimo}` blocks should be processed by the marimo plugin.

**Step 3: Test the interactive blocks locally**

Run: `uv run mkdocs serve`
Expected: Open `http://localhost:8000/examples/period-codes/` in a browser. The text input should be visible and reactive -- typing a period code should update the decoded output.

**Step 4: Commit**

```bash
git add docs/examples/period-codes.md
git commit -m "docs: add interactive Period Codes & Column Resolution page"
```

---

### Task 8: Verify the full site builds and serves correctly

**Files:** None (verification only)

**Step 1: Clean build**

Run: `rm -rf site && uv run mkdocs build -s`
Expected: Build succeeds with no errors. Warnings about strict mode are acceptable if they relate to external links.

**Step 2: Check all pages exist**

Run: `ls site/index.html site/getting-started/index.html site/api-reference/index.html site/examples/exploring-cbs-data/index.html site/examples/population-data/index.html site/examples/period-codes/index.html`
Expected: All six files exist.

**Step 3: Serve and manually verify**

Run: `uv run mkdocs serve`
Expected: Navigate to each page at `localhost:8000` and verify:

- Home: badges render, links work
- Getting Started: code blocks are syntax-highlighted, output blocks display correctly
- API Reference: docstrings are rendered for Client, Column, TableMetadata, and exceptions
- Exploring CBS Data: code examples display clearly
- Population Data: tables render correctly, admonition box appears
- Period Codes: marimo interactive blocks load and respond to input

**Step 4: Commit (if any fixes were needed)**

Only commit if fixes were required during verification.

---

### Task 9: Final commit and cleanup

**Files:**
- Modify: `Makefile` (optional: add docs-related target)

**Step 1: Remove stale docs/modules.md if it still exists**

Run: `test -f docs/modules.md && git rm docs/modules.md || echo "Already removed"`

**Step 2: Run the full test suite to make sure nothing broke**

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml`
Expected: All tests pass.

**Step 3: Run linting**

Run: `uv run pre-commit run -a`
Expected: All checks pass.

**Step 4: Final commit if needed**

```bash
git add -A
git commit -m "docs: complete documentation site with interactive examples"
```

---

## Task Dependency Graph

```
Task 1 (deps + config)
  ├── Task 2 (home page)
  ├── Task 3 (getting started)
  ├── Task 4 (API reference)
  ├── Task 5 (exploring CBS data)
  ├── Task 6 (population data)
  └── Task 7 (interactive period codes)
      └── Task 8 (verify full site)
          └── Task 9 (cleanup + final commit)
```

Tasks 2-7 can be done in parallel after Task 1 completes.
Task 8 depends on all of Tasks 2-7.
Task 9 depends on Task 8.
