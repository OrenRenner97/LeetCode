import random

import pytest

from biz.infra.rowkeys import (STORAGES, KeyOverflow, KeyScheme, audit, compare_sequential, decode, encode,
                               max_safe_width, region_loads)


def test_encode_example():
    s = KeyScheme("int64")
    assert s.width == 18
    assert encode(1_000_000_123, s) == 321_000_000_100_000_000
    assert decode(321_000_000_100_000_000, s) == 1_000_000_123
    assert encode(1_000_000_123, KeyScheme("int64", reverse=False)) == 1_000_000_123
    assert encode(42, KeyScheme("string", 6)) == "240000"
    assert encode(42, KeyScheme("string", 6, reverse=False)) == "000042"


def test_max_safe_width():
    assert {s: max_safe_width(s) for s in STORAGES} == {"int32": 9, "int64": 18, "uint64": 19, "string": 20}
    # Определение: 10^w − 1 влезает, 10^(w+1) − 1 — нет.
    for s, (hi, w) in {"int32": (2**31 - 1, 9), "int64": (2**63 - 1, 18), "uint64": (2**64 - 1, 19)}.items():
        assert 10**w - 1 <= hi < 10 ** (w + 1) - 1, s


@pytest.mark.parametrize("storage", list(STORAGES))
@pytest.mark.parametrize("reverse", [True, False])
def test_roundtrip_and_bijection(storage, reverse):
    s = KeyScheme(storage, reverse=reverse)
    rng = random.Random(3)
    ids = [0, 1, 10, s.max_id, s.max_id - 1] + [rng.randint(0, s.max_id) for _ in range(2000)]
    keys = [encode(i, s) for i in ids]
    assert all(decode(k, s) == i for i, k in zip(ids, keys))
    assert len(set(keys)) == len(set(ids))
    small = KeyScheme(storage, 3, reverse)
    assert sorted(decode(encode(i, small), small) for i in range(1000)) == list(range(1000))
    assert len({encode(i, small) for i in range(1000)}) == 1000


def test_safe_schemes_never_overflow():
    for storage in ("int32", "int64", "uint64"):
        s = KeyScheme(storage)
        assert s.safe
        assert audit([s.max_id, s.max_id - 1, 10 ** (s.width - 1) - 1, 9, 99, 999], s) == []


def test_unsafe_width_overflows_like_leetcode7():
    s = KeyScheme("int64", 19)
    assert not s.safe
    assert encode(1_000_000_009, s) == 9_000_000_001_000_000_000          # 9.0·10¹⁸ ≤ 2⁶³ − 1 ≈ 9.22·10¹⁸
    with pytest.raises(KeyOverflow) as e:
        encode(1_000_000_099, s)                                           # 9.9·10¹⁸
    assert e.value.id == 1_000_000_099
    bad = audit(range(10**9, 10**9 + 10_000), s)
    assert 0.06 < len(bad) / 10_000 < 0.09                                 # ~7.8%: id на …9 с большой предпоследней
    assert all(str(i)[-1] == "9" for i in bad)
    # int32 и width 10: хоть все id и < 2³¹, ключи до 10¹⁰ — переполнение уже на id 3 (ключ 3·10⁹)
    s32 = KeyScheme("int32", 10)
    assert encode(1, s32) == 1_000_000_000
    with pytest.raises(KeyOverflow):
        encode(3, s32)
    with pytest.raises(KeyOverflow):                                       # сам id больше int32
        encode(2**31, s32)
    with pytest.raises(KeyOverflow):
        encode(2**31, KeyScheme("int32", 10, reverse=False))


def test_hotspot_sequential():
    rep = compare_sequential(1_000_000_000, 50_000, KeyScheme("int64"), 16)
    assert rep["direct"].regions_touched == 1 and rep["direct"].hottest_share == 1.0 and rep["direct"].skew == 16
    assert rep["reversed"].regions_touched == 16 and rep["reversed"].skew < 1.01
    assert rep["direct"].total == rep["reversed"].total == 50_000


def test_region_loads_string_and_ten_regions():
    s = KeyScheme("string", 6)
    r = region_loads(range(100, 200), s, 10)
    assert r.loads == (10,) * 10       # первая цифра ключа = последняя цифра id
    assert region_loads([], s, 4).skew == 0.0 and region_loads([], s, 4).hottest_share == 0.0


def test_validation():
    with pytest.raises(ValueError):
        KeyScheme("int128")
    for w in (0, -1, 2.0, True):
        with pytest.raises(ValueError):
            KeyScheme("int64", w)
    with pytest.raises(TypeError):
        KeyScheme("int64", 5, reverse=1)
    s = KeyScheme("int64", 5)
    for bad in (-1, 10**5, 1.0, True, "1"):
        with pytest.raises(ValueError):
            encode(bad, s)
    for bad in (10**5, -1, "12", True):
        with pytest.raises(ValueError):
            decode(bad, s)
    for bad in ("1234", "12a45", 12345, "١٢٣٤٥"):
        with pytest.raises(ValueError):
            decode(bad, KeyScheme("string", 5))
    with pytest.raises(ValueError):
        region_loads([1], s, 0)
    with pytest.raises(ValueError):
        compare_sequential(0, 0, s, 4)
