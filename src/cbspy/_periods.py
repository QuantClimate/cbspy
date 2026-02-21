import re

_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

_YEARLY = re.compile(r"^(\d{4})JJ00$")
_HALFYEARLY = re.compile(r"^(\d{4})HJ0([12])$")
_QUARTERLY = re.compile(r"^(\d{4})KW0([1-4])$")
_MONTHLY = re.compile(r"^(\d{4})MM(\d{2})$")


def decode_period(raw: str) -> str:
    """Decode a CBS period code to a human-readable label.

    Examples:
        2023JJ00 -> "2023"
        2023HJ01 -> "2023 H1"
        2023KW01 -> "2023 Q1"
        2023MM03 -> "2023 March"
    """
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
