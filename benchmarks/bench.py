"""Общий бенчмарк: прогоняет несколько реализаций на входах разного размера.

Пример:
    from common.bench import bench

    bench(
        impls={"hash": two_sum_hash, "sort": two_sum_sort},
        make_input=lambda n: (gen_nums(n), target),   # -> кортеж аргументов
        sizes=[10**3, 10**5, 10**7],
    )
"""
from __future__ import annotations

import gc
import statistics
import time
from typing import Any, Callable, Iterable


def _fmt(sec: float) -> str:
    for unit, k in (("s", 1), ("ms", 1e3), ("µs", 1e6)):
        if sec * k >= 1:
            return f"{sec * k:8.2f} {unit}"
    return f"{sec * 1e9:8.0f} ns"


def bench(
    impls: dict[str, Callable[..., Any]],
    make_input: Callable[[int], tuple],
    sizes: Iterable[int],
    repeat: int = 5,
    warmup: int = 1,
    check: bool = True,
) -> dict[int, dict[str, float]]:
    """Возвращает {n: {impl_name: median_seconds}} и печатает таблицу.

    warmup нужен для JIT (numba) и прогрева GPU: эти прогоны не считаются.
    check=True сверяет, что все реализации вернули одинаковый результат.
    """
    results: dict[int, dict[str, float]] = {}
    names = list(impls)
    width = max(map(len, names)) + 2

    for n in sizes:
        args = make_input(n)
        row: dict[str, float] = {}
        outputs: dict[str, Any] = {}
        for name, fn in impls.items():
            for _ in range(warmup):
                outputs[name] = fn(*args)
            times = []
            for _ in range(repeat):
                gc.disable()
                t0 = time.perf_counter()
                fn(*args)
                times.append(time.perf_counter() - t0)
                gc.enable()
            row[name] = statistics.median(times)

        if check:
            ref_name, ref = next(iter(outputs.items()))
            for name, out in outputs.items():
                if _normalize(out) != _normalize(ref):
                    print(f"  ! {name} != {ref_name} at n={n}")

        results[n] = row
        best = min(row.values())
        print(f"\nn = {n:,}")
        for name, t in sorted(row.items(), key=lambda kv: kv[1]):
            print(f"  {name:<{width}}{_fmt(t)}   x{t / best:6.1f}")

    return results


def _normalize(x: Any) -> Any:
    try:
        import numpy as np

        if isinstance(x, np.ndarray):
            x = x.tolist()
    except ImportError:
        pass
    if isinstance(x, (list, tuple)):
        return sorted(map(_normalize, x), key=repr)
    return x
