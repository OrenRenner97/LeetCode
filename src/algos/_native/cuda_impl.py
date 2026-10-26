"""Two Sum на GPU через CuPy: тот же векторный алгоритм, что в vectorized.py."""
import cupy as cp

from .vectorized import _pair_sum

cp.cuda.runtime.getDeviceCount()  # нет драйвера / GPU → исключение → backend недоступен


def pair_sum_cupy(values, target: int):
    v = cp.asarray(values, dtype=cp.int64)
    # lexsort: по значению, при равенстве по индексу. Не полагаемся на стабильность argsort.
    order = cp.lexsort(cp.stack([cp.arange(v.shape[0]), v]))
    return _pair_sum(cp, v, target, order)


def pairs_batch_cupy(v, off, t):
    from .vectorized import _pairs_batch

    def argsort(k):
        return cp.lexsort(cp.stack([cp.arange(k.shape[0]), k]))

    i, j = _pairs_batch(cp, cp.asarray(v), cp.asarray(off), cp.asarray(t), argsort)
    return cp.asnumpy(i), cp.asnumpy(j)


# ---------- длинная арифметика: тот же carry-lookahead, что в vectorized.py ----------
from .limbs import prepare  # noqa: E402


def add_digits_cupy(a, b, base: int):
    from .vectorized import _add_digits

    return cp.asnumpy(_add_digits(cp, *prepare(a, b, cp), base))


def sum_limbs_cupy(M, base: int):
    from .vectorized import _column_sums, column_sums_to_digits

    return column_sums_to_digits(cp.asnumpy(_column_sums(cp, cp.asarray(M, dtype=cp.uint64), base)).tolist(), base)


# ---------- самое длинное окно без повторов: тот же scan, что в vectorized.py ----------
def _cp_stable(k):
    return cp.lexsort(cp.stack([cp.arange(k.shape[0]), k]))


def unique_window_cupy(seq, max_repeats: int):
    from .vectorized import unique_window_numpy

    return unique_window_numpy(seq, max_repeats, xp=cp, argsort=_cp_stable)


def unique_window_batch_cupy(values, off, max_repeats: int):
    from .vectorized import unique_window_batch_numpy

    s, e = unique_window_batch_numpy(values, off, max_repeats, xp=cp, lexsort=cp.lexsort)
    return cp.asnumpy(s), cp.asnumpy(e)
