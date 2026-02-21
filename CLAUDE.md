# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is cbspy?

A Python client for the CBS Statline (Dutch national statistics) OData API. It returns Polars DataFrames with human-readable column names and decoded period labels.

## Commands

```bash
make install       # Create venv with uv, install pre-commit hooks
make check         # Lint (ruff + pre-commit) and type check (ty)
make test          # Run pytest with coverage
make docs          # Serve docs locally (mkdocs)
make docs-test     # Build docs with strict warnings

# Run a single test
uv run python -m pytest tests/test_client.py::TestGetData::test_returns_dataframe_with_resolved_columns -x

# Type checking only
uv run ty check

# Linting only
uv run ruff check src tests
uv run ruff format --check src tests
```

## Architecture

```
src/cbspy/
├── client.py      # Public API: Client class with list_tables(), get_metadata(), get_data()
├── _odata.py      # Internal HTTP layer: ODataClient handles CBS API calls + pagination
├── _periods.py    # Internal: decode_period() converts CBS codes (2023JJ00 → "2023")
├── models.py      # Pydantic models: Column, TableMetadata
└── exceptions.py  # CBSError → TableNotFoundError, APIError
```

**Data flow:** `Client` → `ODataClient` (HTTP + pagination) → raw JSON → column name resolution + period decoding → `pl.DataFrame`

The `Client` class is the only public entry point. It delegates all HTTP to `ODataClient`, which handles OData pagination via `odata.nextLink`. Column names are resolved from `DataProperties` metadata, and `TimeDimension` columns get their CBS period codes decoded to readable strings.

## Key conventions

- **Package manager:** uv (not pip/poetry). All commands run through `uv run`.
- **Build system:** Hatchling. Source layout: `src/cbspy/`.
- **Python:** 3.10+ (uses `from __future__ import annotations` for modern type syntax).
- **Linting:** Ruff with extensive rule set. Line length 120. `ruff format` uses preview mode.
- **Type checker:** ty (not mypy).
- **Testing:** pytest with `respx` for HTTP mocking (mocks `httpx` requests). No live API calls in tests.
- **Pre-commit hooks:** ruff-check, ruff-format, plus standard file checks (trailing whitespace, end-of-file, TOML/YAML/JSON validation).
- **Internal modules** are prefixed with `_` (e.g., `_odata.py`, `_periods.py`). Public API is explicitly defined in `__init__.py.__all__`.
