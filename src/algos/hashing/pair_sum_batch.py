"""Много независимых Two Sum за один вызов. Требует numpy (extra "fast").

Формат CSR (как в разреженных матрицах): все задачи склеены в один плоский массив.
  задача q:  values[offsets[q] : offsets[q + 1]],  target = targets[q]
Пример бизнес-кейса: q = клиент, values = его открытые счета, target = его платёж.
"""
import numpy as np

from .._dispatch import Dispatcher
from .pair_sum import _python as _python_single

# benchmarks/two_sum_parallel.py: numba prange быстрее всех на любой форме нагрузки, GPU второй.
_dispatch = Dispatcher("find_pairs_batch", priority=("numba", "cuda", "numpy", "python"))


def find_pairs_batch(values, offsets, targets, *, backend: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Возвращает (i, j): int64-массивы длины len(targets) с индексами ВНУТРИ своей задачи.
    -1 там, где пары нет. Контракт на каждую задачу такой же, как у find_pair_with_sum.

    numpy/cuda: |values|, |targets| < 2^39 (в копейках это ±5 млрд ₽), задач < 2^23.
    """
    v = np.ascontiguousarray(values, dtype=np.int64)
    off = np.ascontiguousarray(offsets, dtype=np.int64)
    t = np.ascontiguousarray(targets, dtype=np.int64)
    if off.shape[0] != t.shape[0] + 1 or off[0] != 0 or off[-1] != v.shape[0]:
        raise ValueError("offsets должен иметь длину len(targets) + 1, начинаться с 0 и заканчиваться len(values)")
    return _dispatch.resolve(backend, v.shape[0])(v, off, t)


@_dispatch.register("python")
def _python(v, off, t):
    out_i = np.full(t.shape[0], -1, np.int64)
    out_j = np.full(t.shape[0], -1, np.int64)
    vl, ol = v.tolist(), off.tolist()
    for q, target in enumerate(t.tolist()):
        r = _python_single(vl[ol[q]:ol[q + 1]], target)
        if r:
            out_i[q], out_j[q] = r
    return out_i, out_j


_dispatch.register_optional("numpy", "algos._native.vectorized", "pairs_batch_numpy")
_dispatch.register_optional("numba", "algos._native.numba_impl", "pairs_batch_numba")
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "pairs_batch_cupy")

find_pairs_batch.backends = _dispatch.available  # type: ignore[attr-defined]
