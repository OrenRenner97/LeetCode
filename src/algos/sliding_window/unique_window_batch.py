"""Самое длинное окно без лишних повторов — сразу для многих последовательностей. Требует numpy.

Формат CSR, как у find_pairs_batch:  последовательность q = values[offsets[q] : offsets[q + 1]].
Пример: q = источник платежей (IP), values = отпечатки карт его попыток по времени.
"""
import numpy as np

from .._dispatch import Dispatcher
from .unique_window import _python as _python_single

# benchmarks/longest_substring_backends.py: numba prange — 6–10 ms на 10^6 попыток (×17–50 к python);
# numpy-scan медленнее python, GPU упирается в копирование → оба только явно.
_dispatch = Dispatcher("longest_unique_window_batch", priority=("numba", "python", "numpy", "cuda"))


def longest_unique_window_batch(values, offsets, *, max_repeats: int = 1, backend: str | None = None
                                ) -> tuple[np.ndarray, np.ndarray]:
    """Возвращает (starts, ends): int64-массивы длины len(offsets) - 1, индексы ВНУТРИ своей последовательности.
    Контракт на каждую последовательность — как у longest_unique_window (самое левое из самых длинных; пустая → (0, 0)).
    values: одномерный массив/список int или str.
    """
    if max_repeats < 1:
        raise ValueError(f"max_repeats должен быть >= 1, получено {max_repeats}")
    off = np.ascontiguousarray(offsets, dtype=np.int64)
    n = len(values)
    if off.ndim != 1 or off.shape[0] < 1 or off[0] != 0 or off[-1] != n or (np.diff(off) < 0).any():
        raise ValueError("offsets: неубывающий, от 0 до len(values)")
    return _dispatch.resolve(backend, n)(values, off, max_repeats)


@_dispatch.register("python")
def _python(values, off, max_repeats):
    vals = values.tolist() if hasattr(values, "tolist") else list(values)
    ol = off.tolist()
    out_s = np.zeros(len(ol) - 1, np.int64)
    out_e = np.zeros(len(ol) - 1, np.int64)
    for q in range(len(ol) - 1):
        out_s[q], out_e[q] = _python_single(vals[ol[q]:ol[q + 1]], max_repeats)
    return out_s, out_e


_dispatch.register_optional("numba", "algos._native.numba_impl", "unique_window_batch_numba")
_dispatch.register_optional("numpy", "algos._native.vectorized", "unique_window_batch_numpy", min_n=2**62)
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "unique_window_batch_cupy", min_n=2**62)

longest_unique_window_batch.backends = _dispatch.available  # type: ignore[attr-defined]
