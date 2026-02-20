import pytest

from cbspy._periods import decode_period


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2023JJ00", "2023"),
        ("1950JJ00", "1950"),
        ("2023KW01", "2023 Q1"),
        ("2023KW02", "2023 Q2"),
        ("2023KW03", "2023 Q3"),
        ("2023KW04", "2023 Q4"),
        ("2023MM01", "2023 January"),
        ("2023MM06", "2023 June"),
        ("2023MM12", "2023 December"),
    ],
)
def test_decode_period(raw: str, expected: str):
    assert decode_period(raw) == expected


def test_decode_period_unknown_format():
    assert decode_period("UNKNOWN") == "UNKNOWN"


def test_decode_period_strips_whitespace():
    assert decode_period("  2023JJ00  ") == "2023"
