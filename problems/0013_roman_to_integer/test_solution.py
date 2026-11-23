import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    ("III", 3), ("LVIII", 58), ("MCMXCIV", 1994),
    ("I", 1), ("IV", 4), ("V", 5), ("IX", 9), ("X", 10), ("XIV", 14), ("XL", 40), ("XLIV", 44),
    ("XLIX", 49), ("XC", 90), ("XCIX", 99), ("CD", 400), ("CDXLIV", 444), ("D", 500), ("CM", 900),
    ("CMXCIX", 999), ("M", 1000), ("MMXXIV", 2024), ("MMMDCCXLIX", 3749),
    ("MMMDCCCLXXXVIII", 3888), ("MMMCMXCIX", 3999),
]

# Независимый эталон: число → римская запись по разрядам (как в задаче 12).
_FORMS = (
    ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
    ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"),
    ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"),
)


def to_roman(n: int) -> str:
    return "M" * (n // 1000) + _FORMS[2][n // 100 % 10] + _FORMS[1][n // 10 % 10] + _FORMS[0][n % 10]


def test_examples():
    for name, cls in IMPLS.items():
        for s, expected in CASES:
            assert cls().romanToInt(s) == expected, (name, s)


def test_full_range_roundtrip():
    for name, cls in IMPLS.items():
        f = cls().romanToInt
        for n in range(1, 4000):
            assert f(to_roman(n)) == n, (name, n)


def test_input_built_at_runtime():
    # Строки, собранные в рантайме (не литералы), — у них нет закэшированного хэша.
    for name, cls in IMPLS.items():
        assert cls().romanToInt("".join(["M", "C", "M", "X", "C", "I", "V"])) == 1994, name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
