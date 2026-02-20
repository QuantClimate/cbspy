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
