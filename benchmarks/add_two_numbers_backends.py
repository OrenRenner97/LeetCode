"""Шаг 3 для задачи 2: длинное сложение и аудит uint256.   uv run benchmarks/add_two_numbers_backends.py

1. add_digits: одно огромное число (base 2^64, numpy-массивы, случайные лимбы).
2. sum_limbs: аудит N балансов uint256 (N × 4 лимба) против наивных способов.
"""
import numpy as np
from bench import bench

from algos.arithmetic import add_digits, from_digits, sum_limbs
from biz.crypto.ledger import UInt256


def big_pair(n):
    rng = np.random.default_rng(n)
    return (rng.integers(0, 2**64, size=n, dtype=np.uint64, endpoint=False),
            rng.integers(0, 2**64, size=n, dtype=np.uint64, endpoint=False))


def balances(n):
    # Реалистично: старший лимб почти пуст (баланс < 2^200), иначе сумма 10^7 балансов переполнит uint256.
    rng = np.random.default_rng(n)
    M = rng.integers(0, 2**64, size=(n, 4), dtype=np.uint64, endpoint=False)
    M[:, 3] >>= np.uint64(56)
    return (M,)


def by_backend(fn, backends, **kw):
    return {b: (lambda b: lambda *args: fn(*args, backend=b, **kw))(b) for b in backends}


def check(impls, make, n):
    args = make(n)
    ref = None
    for name, f in impls.items():
        out = f(*args)
        out = out.tolist() if hasattr(out, "tolist") else out
        ref = out if ref is None else ref
        assert out == ref, name


if __name__ == "__main__":
    print("################ add_digits: одно число, base 2^64, ndarray ################")
    impls = by_backend(add_digits, add_digits.backends, base=2**64)
    check(impls, big_pair, 50_000)
    bench(impls, big_pair, [1_000, 100_000, 1_000_000], repeat=5, warmup=2, check=False)
    fast = {k: v for k, v in impls.items() if k != "python"}
    bench(fast, big_pair, [10_000_000], repeat=3, warmup=1, check=False)

    print("\n################ аудит: сумма N балансов uint256 (N × 4 лимба) ################")

    def uint256_loop(M):  # как Ledger.audit() до шага 3: N сложений UInt256
        total = UInt256.ZERO
        for row in M.tolist():
            total = total + UInt256(from_digits(row, 2**64))
        return total.limbs

    def python_int_sum(M):  # «читерский» способ: Python int
        from algos.arithmetic import to_digits
        return to_digits(sum(from_digits(r, 2**64) for r in M.tolist()), 2**64)

    impls = {"UInt256 loop": lambda M: list(uint256_loop(M)), "python int sum": python_int_sum,
             **by_backend(sum_limbs, sum_limbs.backends)}
    check(impls, balances, 2_000)
    bench(impls, balances, [1_000, 100_000], repeat=3, warmup=1, check=False)
    fast = {k: v for k, v in impls.items() if k not in ("UInt256 loop",)}
    bench(fast, balances, [1_000_000], repeat=3, warmup=1, check=False)
    fast = {k: v for k, v in fast.items() if k not in ("python int sum", "python")}
    bench(fast, balances, [10_000_000], repeat=3, warmup=1, check=False)
