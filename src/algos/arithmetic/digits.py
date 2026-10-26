"""Длинная арифметика на массивах цифр. LeetCode: 2. Add Two Numbers (обобщённо) + вычитание.

Формат: little-endian, цифра [0] — младший разряд (как в LeetCode 2).
С base = 2**32 / 2**64 цифры называют «лимбами» (limbs): так устроены BigInt в GMP, CPython, uint256 в Ethereum.
"""
from collections.abc import Sequence

from .._dispatch import Dispatcher

# benchmarks/add_two_numbers_backends.py: до ~256 лимбов Python быстрее (накладные расходы FFI),
# дальше numba ≈ C; GPU не выигрывает (копирование туда-обратно дороже одной операции на лимб),
# поэтому в auto не участвует — только явно backend="cuda".
_dispatch = Dispatcher("add_digits", priority=("numba", "c", "numpy", "cuda", "python"))
_sub_dispatch = Dispatcher("sub_digits")
_NATIVE_MAX_GENERIC_BASE = 2**63  # нативные backend'ы: base == 2^64 или base <= 2^63


def add_digits(a: Sequence[int], b: Sequence[int], *, base: int = 10, backend: str | None = None) -> list[int]:
    """Сумма двух чисел, заданных цифрами в системе счисления base (младший разряд первым).

    Результат нормализован: без ведущих нулей, ноль = [0]. Пустой вход считается нулём.
    Вход может содержать ведущие нули ([3, 0, 0] = 3).
    Тип результата = тип входа: list → list[int], numpy-массив → np.ndarray[uint64]
    (держите данные в numpy, чтобы не платить за конвертацию).
    O(max(len(a), len(b))) по времени и памяти.

    ValueError: base < 2 или цифра вне [0, base).
    """
    if base < 2:
        raise ValueError(f"base должен быть >= 2, получено {base}")
    _check(a, base)
    _check(b, base)
    if base != 2**64 and base > _NATIVE_MAX_GENERIC_BASE:
        backend = "python"  # нативный код работает в uint64: при таком base a + b не влезет
    impl = _dispatch.resolve(backend, max(len(a), len(b)))
    return _same_kind(impl(a, b, base), like=_is_array(a) or _is_array(b), base=base)


def sub_digits(a: Sequence[int], b: Sequence[int], *, base: int = 10, backend: str | None = None) -> list[int]:
    """Разность a - b (a >= b) в системе счисления base, младший разряд первым.

    Зеркало add_digits: вместо переноса — заём (borrow). Результат нормализован.
    ValueError: a < b (отрицательных чисел в этом формате нет), base < 2 или цифра вне [0, base).
    """
    if base < 2:
        raise ValueError(f"base должен быть >= 2, получено {base}")
    _check(a, base)
    _check(b, base)
    return _sub_dispatch.resolve(backend, max(len(a), len(b)))(a, b, base)


def to_digits(n: int, base: int = 10) -> list[int]:
    """Неотрицательное число → цифры (младший разряд первым)."""
    if n < 0:
        raise ValueError("только неотрицательные числа")
    out = []
    while True:
        n, d = divmod(n, base)
        out.append(d)
        if not n:
            return out


def from_digits(digits: Sequence[int], base: int = 10) -> int:
    """Цифры (младший разряд первым) → число. Схема Горнера с конца."""
    n = 0
    for d in reversed(digits):
        n = n * base + d
    return n


def _is_array(x) -> bool:
    return hasattr(x, "dtype")


def _same_kind(result, like: bool, base: int):
    if like and not _is_array(result):
        import numpy as np

        return np.asarray(result, dtype=np.uint64 if base <= 2**64 else object)
    if not like and _is_array(result):
        return result.tolist()
    return result


def _check(digits: Sequence[int], base: int) -> None:
    if _is_array(digits):  # numpy: проверка векторно, иначе цикл на Python съест весь выигрыш
        if digits.dtype.kind == "u" and base >= 2 ** (8 * digits.dtype.itemsize):
            return  # uint64 при base 2^64 корректен по построению: не сканируем массив
        if len(digits) and (int(digits.min()) < 0 or int(digits.max()) >= base):
            raise ValueError(f"цифры вне диапазона [0, {base})")
        return
    for k, d in enumerate(digits):
        if not 0 <= d < base:
            raise ValueError(f"цифра {d} в позиции {k} вне диапазона [0, {base})")


@_dispatch.register("python")
def _python(a: Sequence[int], b: Sequence[int], base: int) -> list[int]:
    a = a.tolist() if _is_array(a) else a
    b = b.tolist() if _is_array(b) else b
    if len(a) < len(b):
        a, b = b, a  # a — длиннее: общий участок, потом хвост a
    out = []
    carry = 0
    for k in range(len(b)):
        carry, d = divmod(a[k] + b[k] + carry, base)
        out.append(d)
    for k in range(len(b), len(a)):
        if not carry:  # перенос погас — хвост копируется как есть
            out.extend(a[k:])
            break
        carry, d = divmod(a[k] + carry, base)
        out.append(d)
    if carry:
        out.append(carry)
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out or [0]


@_sub_dispatch.register("python")
def _python_sub(a: Sequence[int], b: Sequence[int], base: int) -> list[int]:
    a = a.tolist() if _is_array(a) else a
    b = b.tolist() if _is_array(b) else b
    out = []
    borrow = 0
    for k in range(max(len(a), len(b))):  # b может быть длиннее за счёт ведущих нулей
        d = (a[k] if k < len(a) else 0) - (b[k] if k < len(b) else 0) - borrow
        borrow = d < 0
        out.append(d + base if borrow else d)
    if borrow:
        raise ValueError("sub_digits: a < b")
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out or [0]


_NEVER_AUTO = 2**62
_dispatch.register_optional("numpy", "algos._native.vectorized", "add_digits_numpy", min_n=1000)
_dispatch.register_optional("numba", "algos._native.numba_impl", "add_digits_numba", min_n=256)
_dispatch.register_optional("c", "algos._native.c_impl", "add_digits_c", min_n=256)
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "add_digits_cupy", min_n=_NEVER_AUTO)

add_digits.backends = _dispatch.available  # type: ignore[attr-defined]
sub_digits.backends = _sub_dispatch.available  # type: ignore[attr-defined]
