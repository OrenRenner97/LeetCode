import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    ("PAYPALISHIRING", 3, "PAHNAPLSIIGYIR"),
    ("PAYPALISHIRING", 4, "PINALSIGYAHRPI"),
    ("A", 1, "A"),
    ("AB", 1, "AB"),                # одна строка: зигзага нет
    ("ABC", 1, "ABC"),
    ("AB", 5, "AB"),                # строк больше, чем символов
    ("ABC", 3, "ABC"),              # строк ровно столько, сколько символов
    ("ABCD", 2, "ACBD"),            # две строки: чётные и нечётные позиции
    ("ABCDE", 4, "ABCED"),          # E уже на диагонали вверх
    ("ABCDEFG", 4, "AGBFCED"),      # ровно один период + возврат в строку 0
    ("a,b.C", 2, "abC,."),          # запятые, точки, регистр
]


def _brute(s: str, r: int) -> str:
    # Эталон по определению: номер строки каждого символа и стабильная сортировка.
    if r == 1:
        return s
    rows, row, step = [], 0, 1
    for _ in s:
        rows.append(row)
        if row + step < 0 or row + step >= r:
            step = -step
        row += step
    return "".join(ch for _, ch in sorted(zip(rows, s), key=lambda p: p[0]))


def test_examples():
    for name, cls in IMPLS.items():
        for s, r, expected in CASES:
            assert cls().convert(s, r) == expected, (name, s, r)


def test_random_against_brute_force():
    rng = random.Random(42)
    alphabet = "abcXYZ,."
    for _ in range(3000):
        n = rng.randint(1, 40)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        r = rng.randint(1, 45)
        expected = _brute(s, r)
        for name, cls in IMPLS.items():
            assert cls().convert(s, r) == expected, (name, s, r)


def test_is_permutation_with_unique_chars():
    # Уникальные символы: ответ однозначно задаёт перестановку индексов.
    s = "".join(chr(0x100 + i) for i in range(300))
    for r in (1, 2, 3, 7, 150, 299, 300, 1000):
        expected = _brute(s, r)
        assert sorted(expected) == sorted(s)
        for name, cls in IMPLS.items():
            assert cls().convert(s, r) == expected, (name, r)


def test_max_size_agree():
    rng = random.Random(7)
    s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.") for _ in range(1000))
    for r in (1, 2, 3, 31, 500, 999, 1000):
        expected = _brute(s, r)
        for name, cls in IMPLS.items():
            assert cls().convert(s, r) == expected, (name, r)


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
