"""Сжатие произвольных значений в плотные id [0, m): нативный код индексирует массивы по id, а не хэширует.

Так устроены колоночные базы (dictionary encoding): строки хранятся один раз, в данных только номера.
"""
import numpy as np


def compact_ids(values) -> tuple[np.ndarray, int]:
    """→ (ids int64 в [0, m), m). Поддерживаются целые числа и строки (одномерно)."""
    if isinstance(values, str):  # np.asarray("abc") — 0-мерный массив, а нам нужны символы
        values = list(values)
    a = np.asarray(values)
    if a.ndim != 1 or a.dtype == object:
        raise TypeError("нативные backend'ы принимают одномерный массив int или str; для прочих хэшируемых — backend='python'")
    if a.size == 0:
        return np.zeros(0, np.int64), 0
    if a.dtype.kind in "iu":
        lo, hi = int(a.min()), int(a.max())
        if hi - lo < 4 * a.size + 1024:  # значения плотные: достаточно сдвига, без сортировки
            return (a.astype(np.int64) - lo), hi - lo + 1
        try:  # разреженные целые: хэш-таблица на numba, O(n)
            from .numba_impl import factorize_int64

            ids, m = factorize_int64(np.ascontiguousarray(a, dtype=np.int64))
            return ids, int(m)
        except ImportError:
            pass
    uniq, inv = np.unique(a, return_inverse=True)  # строки или нет numba: сортировка, O(n log n)
    return inv.astype(np.int64, copy=False), len(uniq)
