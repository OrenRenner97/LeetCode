import importlib.util
import random
import sys
from pathlib import Path

import pytest

from algos import parse_int_prefix
from algos.parsing import IntPrefix

ROOT = Path(__file__).resolve().parents[2]


def _load_problem_tests():
    path = ROOT / "problems" / "0008_string_to_integer_atoi" / "test_solution.py"
    spec = importlib.util.spec_from_file_location("atoi_problem_tests", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


P = _load_problem_tests()


def leetcode(s):
    return r.value if (r := parse_int_prefix(s)) else 0


def test_leetcode_cases():
    for s, expected in P.CASES + P.UNICODE_CASES:
        assert leetcode(s) == expected, s


def test_against_reference():
    rng = random.Random(8)
    for s in P._random_strings(rng, 20_000) + P._near_bounds():
        assert leetcode(s) == P._ref(s), s


def test_none_vs_zero():
    assert parse_int_prefix("abc") is None
    assert parse_int_prefix("") is None
    assert parse_int_prefix("+") is None
    assert parse_int_prefix("-x") is None
    assert parse_int_prefix("0") == IntPrefix(0, 1, False)
    assert parse_int_prefix("-0") == IntPrefix(0, 2, False)
    assert parse_int_prefix("000x") == IntPrefix(0, 3, False)


def test_end_and_clamped():
    assert parse_int_prefix("  30s") == IntPrefix(30, 4, False)
    assert parse_int_prefix("2147483648") == IntPrefix(2**31 - 1, 10, True)
    assert parse_int_prefix("-2147483648") == IntPrefix(-2**31, 11, False)
    assert parse_int_prefix("-" + "9" * 300 + "z") == IntPrefix(-2**31, 301, True)
    assert parse_int_prefix("0" * 300 + "7") == IntPrefix(7, 301, False)   # нули не считаются цифрами числа


def test_bits_signed():
    assert parse_int_prefix("255", bits=8, signed=False) == IntPrefix(255, 3, False)
    assert parse_int_prefix("256", bits=8, signed=False) == IntPrefix(255, 3, True)
    assert parse_int_prefix("-5", bits=8, signed=False) == IntPrefix(0, 2, True)
    assert parse_int_prefix("-0", bits=8, signed=False) == IntPrefix(0, 2, False)
    assert parse_int_prefix("-129", bits=8) == IntPrefix(-128, 4, True)
    assert parse_int_prefix("9" * 100, bits=None).value == int("9" * 100)
    for bits in (1, 7, 8, 16, 33, 64):
        for signed in (True, False):
            lo, hi = (-(1 << bits - 1), (1 << bits - 1) - 1) if signed else (0, (1 << bits) - 1)
            for v in (lo - 1, lo, hi, hi + 1, 0):
                r = parse_int_prefix(str(v), bits=bits, signed=signed)
                assert r.value == min(hi, max(lo, v)), (bits, signed, v)
                assert r.clamped == (not lo <= v <= hi)


def test_bases():
    assert parse_int_prefix("ff", base=16) == IntPrefix(255, 2, False)
    assert parse_int_prefix("FFg", base=16) == IntPrefix(255, 2, False)
    assert parse_int_prefix("1012", base=2) == IntPrefix(5, 3, False)
    assert parse_int_prefix("zz", base=36).value == 36 * 36 - 1
    assert parse_int_prefix("2", base=2) is None
    rng = random.Random(2)
    for _ in range(3000):
        base = rng.randint(2, 36)
        v = rng.randint(-2**40, 2**40)
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        n, out = abs(v), ""
        while True:
            n, d = divmod(n, base)
            out = digits[d] + out
            if not n:
                break
        s = ("-" if v < 0 else "") + out
        assert parse_int_prefix(s, base=base, bits=64).value == v


def test_whitespace():
    assert parse_int_prefix("\t42") is None
    assert parse_int_prefix("\t\n 42", whitespace=" \t\n").value == 42
    assert parse_int_prefix(" 42", whitespace="") is None


def test_validation():
    with pytest.raises(TypeError):
        parse_int_prefix(42)
    with pytest.raises(TypeError):
        parse_int_prefix("1", bits=True)
    with pytest.raises(ValueError):
        parse_int_prefix("1", base=1)
    with pytest.raises(ValueError):
        parse_int_prefix("1", base=37)
    with pytest.raises(ValueError):
        parse_int_prefix("1", bits=0)
