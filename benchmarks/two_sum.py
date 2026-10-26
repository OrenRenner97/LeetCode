"""uv run benchmarks/two_sum.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0001_two_sum"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution  # noqa: E402

from algos import find_pair_with_sum  # noqa: E402


def worst(n):  # пара в самом конце: худший случай
    return list(range(10**7, 10**7 + n - 2)) + [1, 3], 4


learning = {name: cls().twoSum for name, cls in {"Solution": Solution, **ALL}.items()}
library = {f"algos[{b}]": (lambda b: lambda v, t: find_pair_with_sum(v, t, backend=b))(b)
           for b in find_pair_with_sum.backends}

if __name__ == "__main__":
    print("=== все реализации, малые n ===")
    bench({**learning, **library}, worst, [100, 1000, 3000], repeat=3)

    fast = {k: v for k, v in learning.items() if k not in ("Solution", "BruteHalf")}
    print("\n=== без перебора, большие n ===")
    bench({**fast, **library}, worst, [10**4, 10**6], repeat=3)
