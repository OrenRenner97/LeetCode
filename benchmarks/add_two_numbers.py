"""uv run benchmarks/add_two_numbers.py"""
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "problems" / "0002_add_two_numbers"))

from alternatives import ALL  # noqa: E402
from bench import bench  # noqa: E402
from solution import Solution, build, to_list  # noqa: E402


def make_input(n):
    rng = random.Random(n)
    digits = [rng.randint(0, 9) for _ in range(n - 1)] + [rng.randint(1, 9)]
    # Списки строим заново на каждый вызов внутри impl: InPlace портит вход.
    return digits, list(reversed(digits))


def wrap(cls):
    def run(a, b):
        l1, l2 = build(a), build(b)
        return to_list(cls().addTwoNumbers(l1, l2))
    return run


def build_only(a, b):
    build(a), build(b)
    return None


if __name__ == "__main__":
    impls = {"Solution": Solution, **ALL}
    print("=== все реализации (в т.ч. build входа ~ одинаковый у всех) ===")
    bench({"(build only)": build_only, **{k: wrap(v) for k, v in impls.items()}},
          make_input, [100, 900], repeat=5, check=False)

    print("\n=== длинные числа: только итеративные ===")
    it = {k: wrap(impls[k]) for k in ("Solution", "Compact", "InPlace")}
    bench({"(build only)": build_only, **it}, make_input, [10_000, 1_000_000], repeat=3, check=False)
