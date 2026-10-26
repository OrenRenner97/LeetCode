"""Сумма N длинных чисел за один вызов (аудит: Σ балансов == total_supply).

Трюк — carry-save (отложенный перенос): складываем не числа по очереди, а столбцы лимбов,
и только в конце один раз разрешаем переносы между столбцами. Так делают аппаратные
умножители (дерево сумматоров с сохранением переноса).
"""
from collections.abc import Sequence

from .._dispatch import Dispatcher
from .digits import to_digits

# benchmarks/add_two_numbers_backends.py: numba быстрее всех на любом N (10^7 строк за ~40 ms);
# GPU упирается в копирование 320 МБ по PCIe, поэтому только явно backend="cuda".
_dispatch = Dispatcher("sum_limbs", priority=("numba", "numpy", "cuda", "python"))


def sum_limbs(rows, *, base: int = 2**64, backend: str | None = None) -> list[int]:
    """Сумма N чисел; каждое — строка из L лимбов (младший первым), все строки одной длины.

    rows: список последовательностей или numpy-массив (N, L) uint64 (так быстрее).
    Возвращает лимбы суммы (list[int], нормализованные; ноль = [0]).
    Нативные backend'ы: base == 2^64 или base <= 2^32, N < 2^32.
    """
    n = len(rows)
    if n == 0:
        return [0]
    if not (base == 2**64 or 2 <= base <= 2**32) or n >= 2**32:
        backend = "python"
    return _dispatch.resolve(backend, n)(rows, base)


@_dispatch.register("python")
def _python(rows: Sequence[Sequence[int]], base: int) -> list[int]:
    rows = rows.tolist() if hasattr(rows, "dtype") else rows
    cols = [0] * len(rows[0])
    for row in rows:
        if len(row) != len(cols):
            raise ValueError("все строки должны быть одной длины (дополните нулями)")
        for k, x in enumerate(row):
            cols[k] += x
    return to_digits(sum(c * base**k for k, c in enumerate(cols)), base)


_dispatch.register_optional("numpy", "algos._native.vectorized", "sum_limbs_numpy", min_n=100)
_dispatch.register_optional("numba", "algos._native.numba_impl", "sum_limbs_numba", min_n=100)
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "sum_limbs_cupy", min_n=2**62)

sum_limbs.backends = _dispatch.available  # type: ignore[attr-defined]
