# cbspy Documentation Site Design

## Summary

Build a comprehensive documentation site for cbspy using MkDocs + Material for MkDocs + mkdocs-marimo. The site includes static pages (home, getting started, API reference) and three interactive Marimo notebook pages that let readers explore the CBS Statline API directly in the browser.

## Architecture

- **Static site generator:** MkDocs with Material for MkDocs theme (existing setup)
- **Interactive code:** mkdocs-marimo plugin -- enables `python {marimo}` code fences in markdown that become reactive in the browser
- **API docs:** mkdocstrings with Python handler (existing setup)
- **No separate build step** for Marimo -- the plugin handles transformation during `mkdocs build`

## Site Structure

```
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api-reference.md
  - Interactive Examples:
    - Exploring CBS Data: examples/exploring-cbs-data.md
    - Working with Population Data: examples/population-data.md
    - Period Codes & Column Resolution: examples/period-codes.md
```

## Page Descriptions

### Home (index.md)
Project overview with badges, one-line description, install command, and links to other sections.

### Getting Started (getting-started.md)
Installation instructions (pip, uv), minimal code examples for all three Client methods (list_tables, get_metadata, get_data), and explanation of what cbspy does.

### API Reference (api-reference.md)
Auto-generated from docstrings using mkdocstrings. Covers:
- `Client` class and its three methods
- `Column` and `TableMetadata` Pydantic models
- `CBSError`, `TableNotFoundError`, `APIError` exceptions

### Interactive Example 1: Exploring CBS Data
Let readers discover what CBS Statline offers:
- Table listing with language toggle (EN/NL)
- Select a table and inspect its metadata
- Fetch a data preview

Uses `mo.ui.dropdown` and `mo.ui.radio` for interactivity.

### Interactive Example 2: Working with Population Data
Focused walkthrough using dataset `37296eng` (Population; key figures):
- Fetch population data for specific years
- Display DataFrame with human-readable columns
- Demonstrate period filtering
- Simple population growth analysis

### Interactive Example 3: Period Codes & Column Resolution
Explain cbspy's transformation logic:
- Raw CBS period codes and their decoded forms
- Interactive period code decoder (type a code, see the result)
- Raw column IDs vs. resolved human-readable names
- Column resolution flow explanation

## Dependencies

Add to `pyproject.toml` dev dependencies:
```
"mkdocs-marimo>=0.1",
"marimo>=0.12",
```

## File Layout

```
docs/
  index.md
  getting-started.md
  api-reference.md
  examples/
    exploring-cbs-data.md
    population-data.md
    period-codes.md
```

## mkdocs.yml Changes

- Add `marimo` to plugins list
- Add `admonition`, `pymdownx.highlight`, `pymdownx.superfences`, `pymdownx.tabbed` extensions
- Update nav to include all new pages

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build tool | MkDocs (not Zensical) | Mature, mkdocs-marimo plugin support |
| Interactivity | mkdocs-marimo inline blocks | Native integration, no separate build step |
| API docs | mkdocstrings | Already configured, auto-generates from docstrings |
| Notebook count | 3 | Covers discovery, practical use, and internals |
