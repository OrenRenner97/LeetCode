"""uint256 как в EVM: 4 лимба по 64 бита, проверяемая арифметика (как в Solidity >= 0.8).

Почему не просто int? В Python int и так бесконечный, но:
  1. нужна точная семантика EVM: переполнение 2^256 — это ошибка, а не «большое число»;
  2. фиксированные лимбы — формат для векторизации: миллион балансов = массив (N, 4) uint64,
     его можно отдать numpy/numba/GPU. С Python int так нельзя (это шаг 3).
"""
from __future__ import annotations

from functools import total_ordering

from algos.arithmetic import add_digits, from_digits, sub_digits, to_digits

BASE = 2**64
LIMBS = 4
MAX = 2**256 - 1


class Uint256Overflow(ArithmeticError):
    """Результат >= 2^256 (в Solidity: panic 0x11)."""


class Uint256Underflow(ArithmeticError):
    """Результат < 0 (в Solidity: panic 0x11)."""


@total_ordering
class UInt256:
    __slots__ = ("_limbs",)

    def __init__(self, value: int = 0):
        if not 0 <= value <= MAX:
            raise Uint256Overflow(f"{value} вне диапазона uint256")
        self._limbs: tuple[int, ...] = tuple(to_digits(value, BASE))

    @classmethod
    def _from_limbs(cls, limbs: list[int]) -> UInt256:
        if len(limbs) > LIMBS:  # перенос вылез в 5-й лимб: >= 2^256
            raise Uint256Overflow("uint256 overflow")
        obj = cls.__new__(cls)
        obj._limbs = tuple(limbs)
        return obj

    @classmethod
    def from_hex(cls, s: str) -> UInt256:
        return cls(int(s, 16))

    @property
    def limbs(self) -> tuple[int, ...]:
        """Нормализованные лимбы, младший первым."""
        return self._limbs

    def __add__(self, other: UInt256) -> UInt256:
        return UInt256._from_limbs(add_digits(self._limbs, other._limbs, base=BASE))

    def __sub__(self, other: UInt256) -> UInt256:
        try:
            return UInt256._from_limbs(sub_digits(self._limbs, other._limbs, base=BASE))
        except ValueError:
            raise Uint256Underflow("uint256 underflow") from None

    def __int__(self) -> int:
        return from_digits(self._limbs, BASE)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UInt256) and self._limbs == other._limbs

    def __lt__(self, other: UInt256) -> bool:
        # Лимбы нормализованы: больше лимбов = больше число; при равной длине сравниваем со старшего.
        a, b = self._limbs, other._limbs
        return (len(a), a[::-1]) < (len(b), b[::-1])

    def __hash__(self) -> int:
        return hash(self._limbs)

    def __bool__(self) -> bool:
        return self._limbs != (0,)

    def __repr__(self) -> str:
        return f"UInt256({int(self)})"

    def hex(self) -> str:
        return f"0x{int(self):064x}"


UInt256.ZERO = UInt256(0)  # type: ignore[attr-defined]
UInt256.MAX = UInt256(MAX)  # type: ignore[attr-defined]


def parse_units(amount: str, decimals: int) -> UInt256:
    """'1.5' ETH (decimals=18) → 1500000000000000000 wei. Только строки: float теряет точность."""
    if not isinstance(amount, str):
        raise TypeError("сумму передавайте строкой: float('0.1') уже неточен")
    whole, _, frac = amount.strip().partition(".")
    if not whole.isdigit() and whole != "" or frac and not frac.isdigit() or not (whole or frac):
        raise ValueError(f"некорректная сумма {amount!r}")
    if len(frac) > decimals:
        raise ValueError(f"больше {decimals} знаков после точки: {amount!r}")
    return UInt256(int(whole or "0") * 10**decimals + int(frac.ljust(decimals, "0") or "0"))


def format_units(value: UInt256, decimals: int) -> str:
    """1500000000000000000 wei (decimals=18) → '1.5'."""
    whole, frac = divmod(int(value), 10**decimals)
    frac_s = str(frac).rjust(decimals, "0").rstrip("0") if decimals else ""
    return f"{whole:,}".replace(",", "_") + (f".{frac_s}" if frac_s else "")
