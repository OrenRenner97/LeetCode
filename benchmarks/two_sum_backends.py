"""Шаг 3: все backend'ы find_pair_with_sum.   uv run benchmarks/two_sum_backends.py

Худший случай: пара в самом конце, значения случайно перемешаны.
Две формы входа: list (как придёт из бизнес-слоя) и np.ndarray (данные уже в numpy).
"""
import numpy as np
from bench import bench

from algos import find_pair_with_sum


def worst_ndarray(n):
    rng = np.random.default_rng(0)
    v = rng.permutation(n - 2).astype(np.int64) * 4 + 10**7  # попарные суммы ≠ 4
    return np.concatenate([v, [1, 3]]), 4


def worst_list(n):
    v, t = worst_ndarray(n)
    return v.tolist(), t


def impls(backends):
    return {b: (lambda b: lambda v, t: find_pair_with_sum(v, t, backend=b))(b) for b in backends}


if __name__ == "__main__":
    all_b = find_pair_with_sum.backends
    fast_b = [b for b in all_b if b != "python"]

    print("######## вход: list ########")
    bench(impls(all_b), worst_list, [100, 1_000, 10_000, 100_000, 1_000_000], repeat=5, warmup=2)
    bench(impls(fast_b), worst_list, [10_000_000], repeat=3, warmup=1)

    print("\n######## вход: np.ndarray (без конвертации) ########")
    bench(impls(fast_b), worst_ndarray, [100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000], repeat=5, warmup=2)
