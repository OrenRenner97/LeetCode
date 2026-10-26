"""Пара с заданной суммой. LeetCode: 1. Two Sum (обобщённо)."""
from collections.abc import Sequence

from .._dispatch import Dispatcher

# benchmarks/two_sum_backends.py: GPU выигрывает с ~10^5 (×10 на 10^6), до этого лучше numba.
_dispatch = Dispatcher("find_pair_with_sum", priority=("cuda", "numba", "c", "numpy", "python"))


def find_pair_with_sum(
    values: Sequence[int], target: int, *, backend: str | None = None
) -> tuple[int, int] | None:
    """Индексы (i, j), i < j, такие что values[i] + values[j] == target, или None.

    Если пар несколько, то возвращается пара с минимальным j, а среди них с минимальным i.
    То есть пара, которая «завершается» раньше всех, собранная из самых ранних элементов.
    Если упорядочить values по приоритету (например, по сроку оплаты),
    первыми будут закрыты самые приоритетные элементы.

    O(n) по времени, O(n) по памяти (numpy/cuda: O(n log n)).
    Нативные backend'ы работают в int64: |values|, |target| < 2^62.
    values может быть list, tuple, range или numpy-массивом (так быстрее: без конвертации).
    """
    return _dispatch.resolve(backend, len(values))(values, target)


@_dispatch.register("python")
def _python(values: Sequence[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}
    for j, x in enumerate(values):
        i = seen.get(target - x)
        if i is not None:
            return i, j
        seen.setdefault(x, j)  # первое вхождение = самый ранний индекс
    return None


_dispatch.register_optional("numpy", "algos._native.vectorized", "pair_sum_numpy", min_n=10_000)
_dispatch.register_optional("numba", "algos._native.numba_impl", "pair_sum_numba")
_dispatch.register_optional("c", "algos._native.c_impl", "pair_sum_c")
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "pair_sum_cupy", min_n=300_000)

# Список доступных реализаций: после всех register.
find_pair_with_sum.backends = _dispatch.available  # type: ignore[attr-defined]
