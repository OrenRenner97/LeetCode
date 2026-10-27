"""Шаг 3 для задачи 4.   uv run benchmarks/median_two_sorted_backends.py

1. median_of_sorted(a, b): два int64-массива, разрез. Вызов стоит микросекунды — меряем накладные расходы.
2. kth_of_many_sorted: K шардов по L элементов (бинпоиск по значению), медиана объединения.
3. FairPricer целиком: сколько стоит запрос цены и где на самом деле уходит время.
"""
import time
from datetime import datetime, timedelta

import numpy as np
from bench import bench

from algos import kth_of_many_sorted, kth_of_two_sorted, median_of_sorted
from biz.fintech.fair_price import FairPricer


def by_backend(fn, backends):
    return {b: (lambda b: lambda *a: fn(*a, backend=b))(b) for b in backends}


def two(n):
    rng = np.random.default_rng(n)
    return (np.sort(rng.integers(-10**9, 10**9, n // 2)), np.sort(rng.integers(-10**9, 10**9, n - n // 2)))


def shards(K):
    def make(L):
        rng = np.random.default_rng(K * L)
        return [np.sort(rng.integers(0, 10**9, L)) for _ in range(K)], K * L // 2
    return make


def per_call(fn, number):
    t = time.perf_counter()
    for _ in range(number):
        fn()
    return (time.perf_counter() - t) / number


if __name__ == "__main__":
    print("################ 1. две последовательности (разрез) ################", end="")
    impls = by_backend(median_of_sorted, kth_of_two_sorted.backends)
    impls["python (list)"] = lambda a, b: median_of_sorted(a.tolist(), b.tolist(), backend="python")
    bench({k: v for k, v in impls.items() if k != "python (list)"}, two, [2_000, 100_000, 2_000_000], repeat=2000, warmup=10)
    # tolist() внутри замера стоил бы O(n): отдельно, на заранее сконвертированных списках.
    for n in [2_000, 2_000_000]:
        a, b = (x.tolist() for x in two(n))
        print(f"  python (list), n = {n:,}: {per_call(lambda: median_of_sorted(a, b), 2000) * 1e6:.2f} µs")

    print("\n################ 2. K шардов: kth_of_many_sorted ################", end="")
    for K, L in [(3, 100_000), (10, 100_000), (100, 100_000), (1_000, 1_000), (100, 1_000_000)]:
        print(f"\n--- K = {K}, L = {L:,} ---", end="")
        bench(by_backend(kth_of_many_sorted, kth_of_many_sorted.backends), shards(K), [L], repeat=5, warmup=1)
        arrays, _ = shards(K)(L)
        t = per_call(lambda: np.median(np.concatenate(arrays)), 3)
        print(f"  для сравнения np.median(np.concatenate(...)): {t * 1e3:.2f} ms")

    print("\n################ 3. FairPricer: 5 площадок × 2 000 сделок ################")
    now = datetime(2026, 10, 27, 12)
    rng = np.random.default_rng(0)
    # Сделки за 5 минут, последняя — сейчас: иначе площадки «зависнут» (stale) и расчёт выйдет раньше времени.
    trades = [(f"V{v}", int(28_543 + rng.integers(-20, 21)), now - timedelta(seconds=299 - i * 0.1495))
              for v in range(5) for i in range(2_000)]
    trades.sort(key=lambda t: t[2])
    pricer = FairPricer()
    t = time.perf_counter()
    pricer.add_trades(trades)
    print(f"  add_trade (insort в список):  {(time.perf_counter() - t) / len(trades) * 1e6:6.2f} µs на сделку")
    fp = pricer.fair_price(now)
    assert fp.status.value == "ok" and fp.trades == len(trades), fp  # генератор проверяем до замера
    print(f"  fair_price (медиана + p25/p75 + отсев): {per_call(lambda: pricer.fair_price(now), 200) * 1e6:8.1f} µs")
    tapes = [pricer._tapes[f"V{v}"].prices for v in range(5)]
    k = sum(map(len, tapes)) // 2
    print(f"  из них один kth_of_many_sorted (python, списки): {per_call(lambda: kth_of_many_sorted(tapes, k), 200) * 1e6:6.1f} µs")
    nparr = [np.array(x) for x in tapes]
    for b in kth_of_many_sorted.backends[:-1]:
        print(f"  тот же k-й на numpy-лентах ({b}):  {per_call(lambda: kth_of_many_sorted(nparr, k, backend=b), 200) * 1e6:6.1f} µs")
    print(f"  конвертация 5 лент в numpy на каждый запрос:     "
          f"{per_call(lambda: [np.array(x) for x in tapes], 200) * 1e6:6.1f} µs")
