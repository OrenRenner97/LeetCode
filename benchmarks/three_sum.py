"""uv run benchmarks/three_sum.py

Виды входа (перемешанные):
  wide:   случайные из [-10⁵, 10⁵] (как в LeetCode) — значения почти все различные, троек мало
  narrow: случайные из [-50, 50] — u = 101 различных значений, много повторов
  range:  все числа от -n/2 до n/2 — троек ~ n²/8, время упирается в размер ответа

Перебор O(n³) (Solution, Combinations) — только на n = 300; быстрые — на n = 300 и 3000 (максимум LeetCode).
"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0015_3sum"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

CLASSES = {"Solution": Solution, **ALL}
FAST = {k: v for k, v in ALL.items() if k != "Combinations"}


def gen(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "wide":
            nums = [rng.randint(-10**5, 10**5) for _ in range(n)]
        elif kind == "narrow":
            nums = [rng.randint(-50, 50) for _ in range(n)]
        else:
            nums = list(range(-n // 2, n - n // 2))
            rng.shuffle(nums)
        return (nums,)
    return make


if __name__ == "__main__":
    for kind in ["wide", "narrow", "range"]:
        print(f"\n################ {kind}: все, n = 300 ################")
        bench({name: cls().threeSum for name, cls in CLASSES.items()}, gen(kind), [300], repeat=3, warmup=1)
        print(f"\n################ {kind}: быстрые, n = 3000 ################")
        bench({name: cls().threeSum for name, cls in FAST.items()}, gen(kind), [3000], repeat=5, warmup=1)
