# cbspy

[![Release](https://img.shields.io/github/v/release/thomaspinder/cbspy)](https://img.shields.io/github/v/release/thomaspinder/cbspy)
[![Build status](https://img.shields.io/github/actions/workflow/status/thomaspinder/cbspy/main.yml?branch=main)](https://github.com/thomaspinder/cbspy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/thomaspinder/cbspy/branch/main/graph/badge.svg)](https://codecov.io/gh/thomaspinder/cbspy)
[![License](https://img.shields.io/github/license/thomaspinder/cbspy)](https://img.shields.io/github/license/thomaspinder/cbspy)

A modern Python client for [CBS Statline](https://opendata.cbs.nl) open data that returns Polars DataFrames with human-readable column names.

- **Github repository**: <https://github.com/thomaspinder/cbspy/>
- **Documentation**: <https://thomaspinder.github.io/cbspy/>

## Installation

```bash
pip install cbspy
```

## Quick Start

```python
import cbspy

client = cbspy.Client()

# Discover available tables
tables = client.list_tables(language="en")
print(tables.head())
# shape: (5, 7)
# id, title, description, period, frequency, record_count, modified

# Inspect a table's structure
meta = client.get_metadata("37296eng")
for col in meta.properties:
    print(f"{col.id}: {col.display_name} ({col.unit})")

# Fetch data with human-readable column names
df = client.get_data("37296eng")
print(df.head())
# Columns like "Total population", "Males", "Females" instead of
# "TotalPopulation_1", "Males_2", "Females_3"

# Filter by time period
df = client.get_data("37296eng", periods=["2022JJ00", "2023JJ00"])
```

## Development

```bash
make install    # Create venv and install pre-commit hooks
make test       # Run tests with coverage
make check      # Run linting and type checking
```

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
