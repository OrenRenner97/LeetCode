import random
import time

import pytest

from algos.permutations import zigzag_decode, zigzag_encode, zigzag_order, zigzag_rows, zigzag_split


@pytest.fixture(params=zigzag_encode.backends)
def backend(request):
    return request.param


@pytest.fixture(params=["auto", "by_rows", "by_periods"])
def traversal(request, monkeypatch):
    # Python-backend выбирает обход по порогу; проверяем каждый обход на всех входах.
    from algos.permutations import zigzag as module
    share = {"auto": module._BY_ROWS_MAX_SHARE, "by_rows": 0, "by_periods": 10**18}[request.param]
    monkeypatch.setattr(module, "_BY_ROWS_MAX_SHARE", share)
    return request.param


def _brute_rows(n, rows, mode):
    # Эталон по определению: ходим вниз-вверх, на краю разворачиваемся
    # (snake: на краю стоим ещё один шаг — край повторяется).
    out, row, step = [], 0, 1
    for _ in range(n):
        out.append(row)
        if rows == 1:
            continue
        nxt = row + step
        if not 0 <= nxt < rows:
            step = -step
            nxt = row if mode == "snake" else row + step
        row = nxt
    return out


def _brute_encode(seq, rows, mode):
    r = _brute_rows(len(seq), rows, mode)
    return [x for _, _, x in sorted(zip(r, range(len(seq)), seq))]


MODES = ["zigzag", "snake"]


@pytest.mark.parametrize(
    "seq, rows, expected",
    [
        ("PAYPALISHIRING", 3, "PAHNAPLSIIGYIR"),
        ("PAYPALISHIRING", 4, "PINALSIGYAHRPI"),
        ("A", 1, "A"),
        ("AB", 5, "AB"),
        ("ABCD", 2, "ACBD"),
        ("", 3, ""),
    ],
)
def test_leetcode_examples(backend, traversal, seq, rows, expected):
    assert zigzag_encode(seq, rows, backend=backend) == expected
    assert zigzag_decode(expected, rows, backend=backend) == seq


def test_rows_and_order():
    assert zigzag_rows(7, 3) == [0, 1, 2, 1, 0, 1, 2]
    assert zigzag_rows(7, 3, mode="snake") == [0, 1, 2, 2, 1, 0, 0]
    assert zigzag_rows(4, 1) == [0, 0, 0, 0]
    assert zigzag_rows(4, 1, mode="snake") == [0, 0, 0, 0]
    assert zigzag_rows(0, 3) == []
    assert zigzag_order(7, 3) == [0, 4, 1, 3, 5, 2, 6]


def test_snake_draft():
    # 4 команды, 12 игроков по убыванию силы: 1-й раунд 0→3, 2-й 3→0, 3-й снова 0→3.
    assert zigzag_split(range(12), 4, mode="snake") == [[0, 7, 8], [1, 6, 9], [2, 5, 10], [3, 4, 11]]


@pytest.mark.parametrize("mode", MODES)
def test_random_against_brute(backend, traversal, mode):
    rng = random.Random(6)
    for _ in range(1500):
        n, rows = rng.randint(0, 40), rng.randint(1, 45)
        seq = [rng.randint(0, 5) for _ in range(n)]
        expected = _brute_encode(seq, rows, mode)
        assert zigzag_rows(n, rows, mode=mode) == _brute_rows(n, rows, mode)
        assert zigzag_encode(seq, rows, mode=mode, backend=backend) == expected, (seq, rows)
        assert zigzag_decode(expected, rows, mode=mode, backend=backend) == seq, (seq, rows)
        assert [seq[k] for k in zigzag_order(n, rows, mode=mode)] == expected
        split = zigzag_split(seq, rows, mode=mode)
        assert len(split) == rows and [x for row in split for x in row] == expected


def test_matches_leetcode_solution():
    # По пути к файлу, а не по имени: alternatives.py есть в каждой задаче.
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "problems" / "0006_zigzag_conversion" / "alternatives.py"
    spec = importlib.util.spec_from_file_location("zigzag_alternatives", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ref = module.ALL["RowsList"]()
    rng = random.Random(1)
    for _ in range(500):
        s = "".join(rng.choice("abcXYZ,.") for _ in range(rng.randint(1, 60)))
        r = rng.randint(1, 70)
        assert zigzag_encode(s, r) == ref.convert(s, r)


@pytest.mark.parametrize("mode", MODES)
def test_types_preserved(backend, traversal, mode):
    for seq in ["hello world", b"hello world", bytearray(b"hello world"), tuple(range(11)), list(range(11))]:
        for rows in (1, 3, 20):
            enc = zigzag_encode(seq, rows, mode=mode, backend=backend)
            assert type(enc) is type(seq)
            assert zigzag_decode(enc, rows, mode=mode, backend=backend) == seq
    assert zigzag_encode(range(5), 2) == [0, 2, 4, 1, 3]  # прочие последовательности → list


def test_does_not_mutate_or_alias_mutable_input(backend):
    seq = [1, 2, 3]
    out = zigzag_encode(seq, 5, backend=backend)  # тождественная перестановка
    assert out == seq and out is not seq


def test_numpy(backend, traversal):
    np = pytest.importorskip("numpy")
    a = np.arange(20, dtype=np.int64)
    enc = zigzag_encode(a, 4, backend=backend)
    assert isinstance(enc, np.ndarray) and enc.dtype == a.dtype
    assert enc.tolist() == zigzag_encode(list(range(20)), 4)
    assert (zigzag_decode(enc, 4, backend=backend) == a).all()
    m = np.arange(30).reshape(10, 3)  # многомерный: переставляются строки (первая ось)
    assert (zigzag_encode(m, 3, backend=backend) == m[zigzag_order(10, 3)]).all()


def test_linear_time(backend, traversal):
    # Обход по строкам на rows ~ n медленный по замыслу (~2 µs на строку): поэтому его и выбирают
    # только при малом rows. Здесь проверяем, что auto не попадает в этот случай.
    s = "ab" * 500_000
    for rows in (2, 1000) if traversal == "by_rows" else (2, 1000, 500_000):
        t = time.perf_counter()
        assert zigzag_decode(zigzag_encode(s, rows, backend=backend), rows, backend=backend) == s
        # Ловим квадрат (минуты), а не меряем скорость: by_periods на rows=2 — 500 тыс. периодов,
        # ~2 s на ноутбуке и дрожит от частоты. Лимит 2.0 давал ложные падения.
        assert time.perf_counter() - t < 6.0, rows


def test_validation():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            zigzag_encode("abc", bad)
    for bad in (2.0, True, "3", None):
        with pytest.raises(TypeError):
            zigzag_encode("abc", bad)
    with pytest.raises(ValueError):
        zigzag_encode("abc", 2, mode="spiral")
    with pytest.raises(ValueError):
        zigzag_rows(-1, 2)
    with pytest.raises(TypeError):
        zigzag_order(3.0, 2)
