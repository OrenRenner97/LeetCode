import importlib.util
import random
import re
import sys
import time
from pathlib import Path

import pytest

from algos import compile_pattern, is_match
from algos.automata import ANY, SimplePattern

ROOT = Path(__file__).resolve().parents[2]


def _load_alternatives():
    path = ROOT / "problems" / "0010_regular_expression_matching" / "alternatives.py"
    spec = importlib.util.spec_from_file_location("p10_alternatives", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _random_pattern(rng, n, alphabet="ab."):
    out = ""
    while len(out) < n:
        c = rng.choice(alphabet)
        out += c + "*" if rng.random() < 0.4 else c
    return out[:n].rstrip("*")


def test_leetcode_examples():
    cases = [("aa", "a", False), ("aa", "a*", True), ("ab", ".*", True), ("aab", "c*a*b", True),
             ("mississippi", "mis*is*p*.", False), ("mississippi", "mis*is*ip*.", True),
             ("a", "ab*", True), ("aaa", "a*a", True), ("a", "a.", False), ("bbbba", ".*a*a", True),
             ("", "", True), ("", "a*b*", True), ("", ".", False), ("a", "", False)]
    for s, p, expected in cases:
        assert is_match(s, p, escape=None) is expected, (s, p)


def test_random_against_re_and_nfa():
    nfa = _load_alternatives().TokenNFA()
    rng = random.Random(10)
    for _ in range(5000):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 15)))
        p = _random_pattern(rng, rng.randint(0, 15), "abc.")
        expected = re.fullmatch(p, s) is not None
        assert is_match(s, p) == expected, (s, p)
        if p:
            assert nfa.isMatch(s, p) == expected, (s, p)


def test_escape():
    assert is_match("v1.2", r"v1\.2") and not is_match("v1x2", r"v1\.2")
    assert is_match("a*", r"a\*") and not is_match("aa", r"a\*")
    assert is_match("....", r"\.*") and not is_match("ab", r"\.*")
    assert is_match("\\", r"\\") and is_match("a\\\\", r"a\\*")
    assert is_match("v1x2", "v1.2", escape=None)
    assert is_match("a\\b", "a\\.", escape=None)            # без экранирования '\' — обычная буква
    assert is_match("v1.2", "v1#.2", escape="#") and not is_match("v1x2", "v1#.2", escape="#")
    # сверка с re.escape на случайных шаблонах со спецсимволами
    rng = random.Random(3)
    for _ in range(2000):
        parts, rx = [], []
        for _ in range(rng.randint(0, 6)):
            c = rng.choice("a.*\\")
            lit = c in ".*\\" and rng.random() < 0.6 or c in "*\\"
            parts.append("\\" + c if lit else c)
            rx.append(re.escape(c) if lit else c)
            if rng.random() < 0.3:
                parts.append("*")
                rx.append("*")
        p, r = "".join(parts), "".join(rx)
        s = "".join(rng.choice("a.*\\") for _ in range(rng.randint(0, 6)))
        assert is_match(s, p) == (re.fullmatch(r, s) is not None), (s, p)


def test_no_redos_and_no_recursion():
    k = 30
    pat = compile_pattern("a*" * k + "c")
    t = time.perf_counter()
    assert pat.fullmatch("a" * (2 * k) + "b") is False       # re.fullmatch здесь считал бы годами
    assert time.perf_counter() - t < 0.05
    long = "ab" * 200_000                                    # 400k символов: рекурсия бы упала
    assert compile_pattern(".*b").fullmatch(long)
    assert compile_pattern("a.*").fullmatch(long)
    assert not compile_pattern(".*a").fullmatch(long)


def test_compile_reuse_and_cache():
    p = compile_pattern("a.*")
    assert compile_pattern("a.*") is p                       # lru_cache
    assert [p.fullmatch(s) for s in ("a", "abc", "ba", "")] == [True, True, False, False]
    assert repr(p) == "SimplePattern('a.*')"
    assert p.tokens == (("a", False), (ANY, True))


def test_from_tokens_generic_sequences():
    fraud = SimplePattern.from_tokens([("login", False), ("change_phone", False), (ANY, True), ("payout", False)])
    assert fraud.fullmatch(["login", "change_phone", "payout"])
    assert fraud.fullmatch(["login", "change_phone", "view", "view", "payout"])
    assert not fraud.fullmatch(["login", "view", "payout"])
    nums = SimplePattern.from_tokens([(0, True), (1, False), (ANY, False)])
    assert nums.fullmatch((0, 0, 1, 7)) and not nums.fullmatch((1,))
    with pytest.raises(TypeError):
        SimplePattern.from_tokens([("a", 1)])
    with pytest.raises(TypeError):
        SimplePattern.from_tokens([(["unhashable"], False)])


def test_validation():
    for bad in ("*", "*a", "a**", ".**", "a*\\", "\\"):
        with pytest.raises(ValueError):
            compile_pattern(bad)
    assert compile_pattern(r"\**")                           # литерал '*', повторённый — допустимо
    for bad in (None, 1, b"a*"):
        with pytest.raises(TypeError):
            compile_pattern(bad)
    with pytest.raises(TypeError):
        is_match(None, "a")
    for esc in ("", "ab", ".", "*", 1):
        with pytest.raises(ValueError):
            compile_pattern("a", escape=esc)


def test_step_api_equals_fullmatch():
    rng = random.Random(5)
    for _ in range(2000):
        p = compile_pattern(_random_pattern(rng, rng.randint(0, 10), "abc."))
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 10)))
        state = p.start()
        for ch in s:
            state = p.step(state, ch)
        assert p.accepts(state) == p.fullmatch(s), (s, p)
    p = compile_pattern("ab")
    assert p.step(p.start(), "x") == 0                       # мёртвое состояние
    assert p.step(0, "a") == 0                               # из мёртвого не выйти


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
