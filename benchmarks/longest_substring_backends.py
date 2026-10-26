"""Шаг 3 для задачи 3.   uv run benchmarks/longest_substring_backends.py

1. longest_unique_window: одна последовательность (numpy-массив id).
2. longest_unique_window_batch: много источников, всего 10^6 попыток.
3. Детектор card testing целиком: где на самом деле уходит время + потоковый режим.
"""
import random
import time
from datetime import datetime, timedelta

import numpy as np
from bench import bench

from algos.sliding_window import longest_unique_window, longest_unique_window_batch
from biz.fintech.antifraud import CardTestingDetector, PaymentAttempt, Status, StreamingCardTestingDetector


def by_backend(fn, backends, **kw):
    return {b: (lambda b: lambda *a: fn(*a, backend=b, **kw))(b) for b in backends}


def chars(n):  # 95 «символов» (как в условии) → ответ ~15–20
    return (np.random.default_rng(n).integers(0, 95, size=n),)


def sparse_cards(n):  # id карт до 2^40: сжатие через сортировку (np.unique)
    return (np.random.default_rng(n).integers(0, 2**40, size=n),)


def batch(nq, per):
    def make(_n):
        rng = np.random.default_rng(nq)
        return rng.integers(0, 50, size=nq * per), np.arange(0, nq * per + 1, per)
    return make


def check(impls, args):
    outs = [tuple(np.asarray(x).tolist() for x in f(*args)) if isinstance(f(*args)[0], np.ndarray) else f(*args)
            for f in impls.values()]
    assert all(o == outs[0] for o in outs), "реализации разошлись"


def make_attempts(n_sources, per_source, seed=0):
    rng = random.Random(seed)
    t0 = datetime(2026, 10, 24)
    out = []
    for s in range(n_sources):
        fraud = rng.random() < 0.01
        own = [f"fp{rng.randrange(10**9):09d}" for _ in range(per_source if fraud else rng.randint(1, 2))]
        for k in range(per_source):
            out.append(PaymentAttempt(f"{s}-{k}", t0 + timedelta(seconds=k), f"src{s}",
                                      own[k] if fraud else rng.choice(own), "0000", 100,
                                      Status.DECLINED if fraud and rng.random() < 0.8 else Status.APPROVED))
    rng.shuffle(out)
    return out


def _group(attempts, defaultdict):
    d = defaultdict(list)
    for a in attempts:
        d[a.source].append(a)
    return list(d.values())


def timed(label, fn):
    t = time.perf_counter()
    res = fn()
    print(f"  {label:<46}{time.perf_counter() - t:8.3f} s")
    return res


if __name__ == "__main__":
    print("################ 1. одна последовательность, numpy-массив ################")
    for gen, sizes in [(chars, [1_000, 100_000, 1_000_000, 10_000_000]), (sparse_cards, [100_000, 1_000_000, 10_000_000])]:
        print(f"\n--- {gen.__name__} ---", end="")
        impls = by_backend(longest_unique_window, longest_unique_window.backends)
        impls["python (list)"] = lambda a: longest_unique_window(a.tolist(), backend="python")
        check(impls, gen(5000))
        bench({k: v for k, v in impls.items() if not k.startswith("python")}, gen, sizes, repeat=3, warmup=1, check=False)
        bench({"python (list)": impls["python (list)"], "numba": impls["numba"]}, gen, [1_000_000], repeat=3, warmup=1, check=False)

    print("\n################ 2. batch: всего 10^6 попыток ################")
    for nq, per in [(100_000, 10), (1_000, 1_000)]:
        print(f"\n--- {nq:,} источников × {per:,} попыток ---", end="")
        impls = by_backend(longest_unique_window_batch, longest_unique_window_batch.backends)
        check(impls, batch(200, 30)(0))
        bench(impls, batch(nq, per), [nq * per], repeat=3, warmup=1, check=False)

    print("\n################ 3. детектор целиком: 10^5 источников × 10 попыток ################")
    attempts = timed("генерация 10^6 PaymentAttempt (не в счёт)", lambda: make_attempts(100_000, 10))
    a_py = timed("scan(backend='python')  — по одному источнику", lambda: CardTestingDetector(backend="python").scan(attempts))
    timed("scan(auto)  — прогрев numba (не в счёт)", lambda: CardTestingDetector().scan(attempts[:1000]))
    a_nb = timed("scan(auto)  — один batch-вызов (numba)", lambda: CardTestingDetector().scan(attempts))
    assert [a.source for a in a_py] == [a.source for a in a_nb]

    print("  из чего состоит scan:")
    from collections import defaultdict
    by = timed("    группировка по источнику", lambda: _group(attempts, defaultdict))
    timed("    сортировка внутри источников", lambda: [g.sort(key=lambda a: (a.ts, a.id)) for g in by])
    flat_str = timed("    flat-список отпечатков (строки)", lambda: [a.card_fp for g in by for a in g])
    enc = {}
    flat = timed("    flat-список номеров (dict-кодирование)", lambda: [enc.setdefault(a.card_fp, len(enc)) for g in by for a in g])
    offs = np.cumsum([0] + [len(g) for g in by])
    timed("    batch (numba) на строках: np.unique сортирует", lambda: longest_unique_window_batch(flat_str, offs))
    timed("    batch (numba) на номерах", lambda: longest_unique_window_batch(flat, offs))
    timed("    longest_unique_window_batch (python)", lambda: longest_unique_window_batch(flat, offs, backend="python"))

    stream = StreamingCardTestingDetector()
    ordered = sorted(attempts, key=lambda a: (a.ts, a.id))
    t = time.perf_counter()
    n_alerts = sum(1 for a in ordered if stream.observe(a))
    dt = time.perf_counter() - t
    print(f"  потоковый детектор: {len(ordered) / dt:,.0f} попыток/с, тревог {n_alerts}, источников в памяти {stream.tracked_sources:,}")

