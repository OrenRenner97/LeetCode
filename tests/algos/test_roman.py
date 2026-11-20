import importlib.util
import re
from pathlib import Path

import numpy as np
import pytest

from algos import to_roman
from algos.arithmetic import ROMAN_MAX, ROMAN_MIN

# Каноническая римская запись 1..3999: каждый разряд — одна из десяти форм.
CANON = re.compile(r"M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")
VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _solution():
    path = Path(__file__).resolve().parents[2] / "problems" / "0012_integer_to_roman" / "solution.py"
    spec = importlib.util.spec_from_file_location("p12_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Solution()


def _value(s: str) -> int:
    """Независимый эталон: символ меньше следующего вычитается."""
    vals = [VALUES[c] for c in s]
    return sum(-v if i + 1 < len(vals) and v < vals[i + 1] else v for i, v in enumerate(vals))


def test_leetcode_examples():
    assert to_roman(3749) == "MMMDCCXLIX"
    assert to_roman(58) == "LVIII"
    assert to_roman(1994) == "MCMXCIV"


def test_full_range_against_solution_and_reference():
    sol = _solution()
    for n in range(ROMAN_MIN, ROMAN_MAX + 1):
        r = to_roman(n)
        assert r == sol.intToRoman(n), n
        assert CANON.fullmatch(r) and _value(r) == n, (n, r)


def test_bounds():
    assert (ROMAN_MIN, ROMAN_MAX) == (1, 3999)
    assert to_roman(1) == "I" and to_roman(3999) == "MMMCMXCIX"
    for n in (0, -1, -3999, 4000, 5000, 10**100):
        assert to_roman(n) is None, n
        assert to_roman(n, lowercase=True) is None, n


def test_lowercase():
    assert to_roman(14, lowercase=True) == "xiv"
    assert to_roman(3888, lowercase=True) == "mmmdccclxxxviii"
    for n in range(ROMAN_MIN, ROMAN_MAX + 1, 37):
        assert to_roman(n, lowercase=True) == to_roman(n).lower()


def test_integer_types():
    assert to_roman(np.int64(1994)) == "MCMXCIV"
    assert to_roman(np.uint16(4)) == "IV"
    assert to_roman(np.int32(4000)) is None


@pytest.mark.parametrize("bad", [True, False, 4.0, 4.5, "4", None, [4]])
def test_type_errors(bad):
    with pytest.raises(TypeError):
        to_roman(bad)
