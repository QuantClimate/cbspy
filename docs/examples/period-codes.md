# Period Codes & Column Resolution

CBS Statline uses internal encodings for time periods and column names. cbspy automatically decodes these to human-readable labels. This page explains how the decoding works, with interactive examples you can try in your browser.

## Period code formats

CBS encodes time periods as strings with a specific format:

| Pattern | Example | Decoded |
|---------|---------|---------|
| `YYYYJJnn` | `2023JJ00` | `2023` (yearly) |
| `YYYYHJnn` | `2023HJ01` | `2023 H1` (half-yearly) |
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
_HALFYEARLY = re.compile(r"^(\d{4})HJ0([12])$")
_QUARTERLY = re.compile(r"^(\d{4})KW0([1-4])$")
_MONTHLY = re.compile(r"^(\d{4})MM(\d{2})$")


def decode_period(raw: str) -> str:
    s = raw.strip()
    if m := _YEARLY.match(s):
        return m.group(1)
    if m := _HALFYEARLY.match(s):
        return f"{m.group(1)} H{m.group(2)}"
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
- `2023HJ01` (half-yearly -- H1)
- `2023KW03` (quarterly -- Q3)
- `2023MM12` (monthly -- December)
- `1990JJ00` (older data)

## Batch decoding

Here is a batch of period codes and their decoded values:

```python {marimo}
examples = [
    "2023JJ00", "2022JJ00", "2021JJ00",
    "2023HJ01", "2023HJ02",
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
2. **Half-yearly:** `^\d{4}HJ0[12]$` -- matches codes like `2023HJ01`. Extracts year and half number.
3. **Quarterly:** `^\d{4}KW0[1-4]$` -- matches codes like `2023KW01`. Extracts year and quarter number.
4. **Monthly:** `^\d{4}MM\d{2}$` -- matches codes like `2023MM03`. Extracts year and month number, then maps to the month name.

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
