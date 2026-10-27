"""uv run benchmarks/median_two_sorted.py

Входы (N = m + n, оба массива отсортированы):
  interleaved: случайные числа, массивы перемешаны по значениям, m = n = N/2
  disjoint:    все nums1 < всех nums2 (разрез на краю короткого массива)
  skewed:      m = 10, n = N - 10 (бинпоиск по короткому массиву почти бесплатен)

Меряется только вызов: массивы готовы заранее. Для O(log) решений это и есть
их преимущество — данные уже отсортированы и лежат в памяти.
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0004_median_of_two_sorted_arrays"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

LIM = 10**6


def gen(kind):
    def make(total):
        rng = random.Random(total)
        if kind == "interleaved":
            m = total // 2
            a = sorted(rng.randint(-LIM, LIM) for _ in range(m))
            b = sorted(rng.randint(-LIM, LIM) for _ in range(total - m))
        elif kind == "disjoint":
            m = total // 2
            a = sorted(rng.randint(-LIM, -1) for _ in range(m))
            b = sorted(rng.randint(0, LIM) for _ in range(total - m))
        else:
            a = sorted(rng.randint(-LIM, LIM) for _ in range(10))
            b = sorted(rng.randint(-LIM, LIM) for _ in range(total - 10))
        return a, b
    return make


if __name__ == "__main__":
    impls = {name: cls().findMedianSortedArrays for name, cls in {"Solution": Solution, **ALL}.items()}
    for kind in ["interleaved", "disjoint", "skewed"]:
        print(f"\n################ {kind} ################", end="")
        bench(impls, gen(kind), [2_000, 100_000, 2_000_000], repeat=5, warmup=1)
