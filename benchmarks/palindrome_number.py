"""uv run benchmarks/palindrome_number.py

Вход задачи ограничен (≤ 10 цифр), поэтому меряем пачку из n вызовов: [f(x) for x in xs].
Виды входа:
  random:     равномерно по [−2³¹, 2³¹ − 1] — половина отрицательных, палиндромов почти нет
  positive:   равномерно по [0, 2³¹ − 1] — почти все 10-значные непалиндромы, ранний выход решает
  palindrome: только палиндромы — худший случай: ранних выходов нет, все цифры проверяются
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0009_palindrome_number"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}
INT_MAX, INT_MIN = 2**31 - 1, -2**31


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random":
            xs = [rng.randint(INT_MIN, INT_MAX) for _ in range(n)]
        elif kind == "positive":
            xs = [rng.randint(0, INT_MAX) for _ in range(n)]
        else:
            xs = []
            while len(xs) < n:
                left = str(rng.randint(10**4, 10**5 - 1))     # 10-значные: самые длинные
                p = int(left + left[::-1])
                if p <= INT_MAX:
                    xs.append(p)
        return (xs,)
    return make


def batch(cls):
    f = cls().isPalindrome
    return lambda xs: [f(x) for x in xs]


if __name__ == "__main__":
    impls = {name: batch(cls) for name, cls in CLASSES.items()}
    for kind in ["random", "positive", "palindrome"]:
        print(f"\n################ {kind} ################")
        bench(impls, gen(kind), [100_000], repeat=5, warmup=1)
