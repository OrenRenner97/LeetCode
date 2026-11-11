import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alternatives import ALL, INT_MAX, INT_MIN  # noqa: E402
from solution import Solution  # noqa: E402

IMPLS = {"Solution": Solution, **ALL}

CASES = [
    (123, 321), (-123, -321), (120, 21), (0, 0),
    (1, 1), (-1, -1), (10, 1), (-10, -1), (1000000000, 1),
    (1534236469, 0),            # 9646324351 > 2³¹ − 1
    (INT_MIN, 0),               # −2³¹: модуль сам не влезает в int32, разворот 8463847412
    (INT_MAX, 0),               # 7463847412
    (1463847412, 2147483641),   # влезает впритык
    (-1463847412, -2147483641),
    (1463847413, 0),            # 3147483641: старшая цифра больше
    (1563847412, 0),            # 2147483651: последняя цифра 1 > 7 после равного префикса
    (-1563847412, 0),           # −2147483651 < −2³¹
    (1463847402, 2047483641),   # тот же префикс, меньше — влезает
    (2147447412, 2147447412),   # палиндром у границы
    (-2147447412, -2147447412),
]


def _ref(x: int) -> int:
    # Эталон по определению, на неограниченных int.
    r = int(str(abs(x))[::-1]) * (1 if x >= 0 else -1)
    return r if INT_MIN <= r <= INT_MAX else 0


def _near_bounds():
    # Все x, чей разворот лежит в ±5000 от границ: здесь живут ошибки на единицу.
    out = []
    for bound in (INT_MAX, -INT_MIN):
        for r in range(bound - 5000, bound + 5001):
            x = int(str(r)[::-1])
            if x <= INT_MAX:
                out += [x, -x]
    return out


def test_examples():
    for name, cls in IMPLS.items():
        for x, expected in CASES:
            assert cls().reverse(x) == expected, (name, x)


def test_near_bounds():
    xs = _near_bounds()
    assert len(xs) > 8_000   # ~8.6k из 40k: у остальных x = разворот(r) сам > 2³¹ − 1
    for name, cls in IMPLS.items():
        f = cls().reverse
        for x in xs:
            assert f(x) == _ref(x), (name, x)


def test_random_against_reference():
    rng = random.Random(7)
    xs = [rng.randint(INT_MIN, INT_MAX) for _ in range(20_000)]
    xs += [rng.choice((1, -1)) * rng.randint(0, 10 ** rng.randint(0, 9)) for _ in range(20_000)]
    for name, cls in IMPLS.items():
        f = cls().reverse
        for x in xs:
            assert f(x) == _ref(x), (name, x)


def test_results_fit_int32():
    rng = random.Random(1)
    for name, cls in IMPLS.items():
        f = cls().reverse
        for _ in range(5000):
            assert INT_MIN <= f(rng.randint(INT_MIN, INT_MAX)) <= INT_MAX, name


if __name__ == "__main__":  # можно запустить и без pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all tests passed")
