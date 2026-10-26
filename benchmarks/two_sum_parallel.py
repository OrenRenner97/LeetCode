"""Шаг 3: многопоточность vs мультипроцессинг vs numba prange vs GPU.
uv run benchmarks/two_sum_parallel.py

Бизнес-нагрузка: Q клиентов × k открытых счетов, у каждого клиента один платёж.
Во всех сценариях всего 2 млн счетов, меняется только форма: много мелких или мало крупных задач.
"""
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np
from bench import bench

from algos import find_pair_with_sum
from algos.hashing import find_pairs_batch

WORKERS = os.cpu_count()


def make_batch(q, k, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.integers(1, 10**8, size=q * k, dtype=np.int64)  # счета в копейках
    off = np.arange(0, q * k + 1, k, dtype=np.int64)
    t = rng.integers(1, 2 * 10**8, size=q, dtype=np.int64)
    has_pair = rng.random(q) < 0.5  # у половины клиентов платёж = сумма двух счетов
    a, b = rng.integers(0, k, size=q), rng.integers(0, k, size=q)
    idx = np.nonzero(has_pair & (a != b))[0]
    t[idx] = v[off[idx] + a[idx]] + v[off[idx] + b[idx]]
    return v, off, t


def _chunks(q):
    bounds = np.linspace(0, q, WORKERS * 4 + 1, dtype=np.int64)
    return [(int(a), int(b)) for a, b in zip(bounds[:-1], bounds[1:]) if b > a]


def _slice(v, off, t, a, b):
    return v[off[a]:off[b]], off[a:b + 1] - off[a], t[a:b]


def _py_chunk(args):
    return find_pairs_batch(*args, backend="python")


def _single_loop(backend):
    def run(args):
        v, off, t = args
        out_i = np.full(t.shape[0], -1, np.int64)
        out_j = np.full(t.shape[0], -1, np.int64)
        for q in range(t.shape[0]):
            r = find_pair_with_sum(v[off[q]:off[q + 1]], int(t[q]), backend=backend)
            if r:
                out_i[q], out_j[q] = r
        return out_i, out_j
    return run


def _merge(parts):
    parts = list(parts)  # map() отдаёт итератор, а проходим дважды
    return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])


def strategies(proc_pool, thread_pool):
    def processes_python(v, off, t):
        # Мультипроцессинг: нет GIL, но данные сериализуются (pickle) и копируются в каждый процесс.
        return _merge(proc_pool.map(_py_chunk, [_slice(v, off, t, a, b) for a, b in _chunks(t.shape[0])]))

    def threads(backend):
        # Потоки: данные общие, без копирования. Но Python-цикл по клиентам держит GIL,
        # отпускается он только внутри C (ctypes) / numba (nogil).
        fn = _single_loop(backend)

        def run(v, off, t):
            return _merge(thread_pool.map(fn, [_slice(v, off, t, a, b) for a, b in _chunks(t.shape[0])]))
        return run

    s = {
        "seq: python": lambda v, o, t: find_pairs_batch(v, o, t, backend="python"),
        f"processes×{WORKERS}: python": processes_python,
        f"threads×{WORKERS}: python": threads("python"),
        f"threads×{WORKERS}: c (ctypes, GIL off)": threads("c"),
        "seq: c (цикл по клиентам)": lambda v, o, t: _single_loop("c")((v, o, t)),
    }
    for b in find_pairs_batch.backends:
        if b != "python":
            label = {"numba": f"numba prange×{WORKERS}", "numpy": "numpy vectorized", "cuda": "cuda (cupy)"}[b]
            s[label] = (lambda b: lambda v, o, t: find_pairs_batch(v, o, t, backend=b))(b)
    return s


if __name__ == "__main__":
    with ProcessPoolExecutor(WORKERS) as pp, ThreadPoolExecutor(WORKERS) as tp:
        impls = strategies(pp, tp)

        # Сверка: все стратегии дают один и тот же ответ.
        ref = None
        for name, fn in impls.items():
            out = fn(*make_batch(2_000, 50, seed=1))
            ref = ref or out
            assert all((a == b).all() for a, b in zip(out, ref)), name

        for q, k in [(200_000, 10), (2_000, 1_000), (20, 100_000)]:
            print(f"\n######## {q:,} клиентов × {k:,} счетов ########", end="")
            data = make_batch(q, k)
            bench(impls, lambda _n, data=data: data, [q * k], repeat=3, warmup=1, check=False)
