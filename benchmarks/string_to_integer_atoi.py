"""uv run benchmarks/string_to_integer_atoi.py

Вход задачи ограничен (≤ 200 символов), поэтому меряем пачку из n вызовов: [f(s) for s in xs].
Виды входа:
  typical:  «  -1234abc»: 0–3 пробела, знак, 1–10 цифр, хвост — как в примерах задачи
  garbage:  первый значащий символ — буква: ответ 0 почти сразу
  long:     ~200 символов: пробелы, нули и длинное число — переполнение
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0008_string_to_integer_atoi"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}


def gen(kind):
    def make(n):
        rng = random.Random(n)
        xs = []
        for _ in range(n):
            if kind == "typical":
                s = (" " * rng.randint(0, 3) + rng.choice(("", "+", "-"))
                     + str(rng.randint(0, 10 ** rng.randint(1, 10))) + rng.choice(("", "abc", " 42", ".5")))
            elif kind == "garbage":
                s = " " * rng.randint(0, 3) + rng.choice("abcxyz.") + str(rng.randint(0, 10**6))
            else:
                k = rng.randint(0, 40)
                s = (" " * k + rng.choice(("+", "-")) + "0" * rng.randint(0, 40)
                     + "".join(rng.choice("0123456789") for _ in range(198 - k - 40)))
            xs.append(s)
        return (xs,)
    return make


def batch(cls):
    f = cls().myAtoi
    return lambda xs: [f(s) for s in xs]


if __name__ == "__main__":
    impls = {name: batch(cls) for name, cls in CLASSES.items()}
    for kind in ["typical", "garbage", "long"]:
        print(f"\n################ {kind} ################")
        bench(impls, gen(kind), [100_000], repeat=5, warmup=1)
