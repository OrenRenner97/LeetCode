"""uv run benchmarks/container_with_most_water.py

Один вызов на массиве длины n. Виды входа:
  random:     высоты равномерно в [0, 10⁴] — пропуск низких линий срабатывает часто
  increasing: 0, 1, 2, … — каждая следующая линия выше: пропускать нечего
  equal:      все 10⁴ — ответ на первом шаге, но указатели всё равно идут до встречи
  hill:       горка: низко по краям, высоко в середине — указатели долго ползут вверх
BruteForce — только при n = 10³ (O(n²)).
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0011_container_with_most_water"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "random":
            h = [rng.randint(0, 10_000) for _ in range(n)]
        elif kind == "increasing":
            h = [i * 10_000 // n for i in range(n)]
        elif kind == "equal":
            h = [10_000] * n
        else:
            h = [min(i, n - 1 - i) * 20_000 // n for i in range(n)]
        return (h,)
    return make


if __name__ == "__main__":
    for kind in ["random", "increasing", "equal", "hill"]:
        print(f"\n################ {kind} ################")
        small = {name: cls().maxArea for name, cls in CLASSES.items()}
        bench(small, gen(kind), [1_000], repeat=5, warmup=1)
        big = {name: cls().maxArea for name, cls in CLASSES.items() if name != "BruteForce"}
        bench(big, gen(kind), [100_000], repeat=5, warmup=1)
