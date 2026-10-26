"""Учёт токена в стиле ERC-20: mint / burn / transfer, журнал событий, аудит.

Поведение повторяет смарт-контракт:
  - вся арифметика проверяемая (uint256 overflow / underflow → откат);
  - операция атомарна: при ошибке состояние не меняется (в EVM это revert);
  - инвариант: сумма всех балансов == total_supply.
"""
import re
from collections.abc import Iterable
from dataclasses import dataclass

from algos.arithmetic import from_digits, sum_limbs

from .uint256 import LIMBS, UInt256, format_units

ZERO_ADDRESS = "0x" + "0" * 40
_ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")


class InsufficientBalance(Exception):
    pass


class InvalidAddress(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    symbol: str
    decimals: int  # ETH = 18, USDT/USDC = 6, BTC = 8


@dataclass(frozen=True)
class TransferEvent:
    """Как событие Transfer(from, to, value) в ERC-20. mint: from = 0x0, burn: to = 0x0."""
    frm: str
    to: str
    value: UInt256


@dataclass(frozen=True)
class AuditResult:
    ok: bool
    balances_sum: int  # обычный int: сумма испорченных балансов может и не влезть в uint256
    total_supply: UInt256
    holders: int


def audit_balances(balances: Iterable[UInt256], total_supply: UInt256, backend: str | None = None) -> AuditResult:
    """Σ балансов == total_supply? Без состояния: годится и для Ledger, и для снимка из блокчейна.

    Не складываем балансы по одному через UInt256 (N раз прогонять перенос),
    а суммируем столбцы лимбов разом (carry-save, algos.sum_limbs): на 10^5 держателей ~4000× быстрее.
    """
    rows = [b.limbs + (0,) * (LIMBS - len(b.limbs)) for b in balances]
    total = from_digits(sum_limbs(rows, base=2**64, backend=backend), 2**64) if rows else 0
    return AuditResult(total == int(total_supply), total, total_supply, len(rows))


def _addr(a: str) -> str:
    if not _ADDRESS.match(a):
        raise InvalidAddress(f"некорректный адрес {a!r}")
    return a.lower()  # EIP-55 checksum (регистр букв) не проверяем, приводим к нижнему


class Ledger:
    def __init__(self, token: Token, backend: str | None = None):
        self.token = token
        self.backend = backend  # для audit(): None → auto (numba на больших N)
        self.total_supply = UInt256.ZERO
        self.events: list[TransferEvent] = []
        self._balances: dict[str, UInt256] = {}

    def balance_of(self, address: str) -> UInt256:
        return self._balances.get(_addr(address), UInt256.ZERO)

    def mint(self, to: str, amount: UInt256) -> None:
        to = _addr(to)
        if to == ZERO_ADDRESS:
            raise InvalidAddress("mint на нулевой адрес")
        # Сначала считаем всё, потом пишем: если что-то переполнится, состояние не тронуто.
        new_supply = self.total_supply + amount
        new_balance = self.balance_of(to) + amount
        self.total_supply = new_supply
        self._balances[to] = new_balance
        self.events.append(TransferEvent(ZERO_ADDRESS, to, amount))

    def burn(self, frm: str, amount: UInt256) -> None:
        frm = _addr(frm)
        new_balance = self._debit(frm, amount)
        new_supply = self.total_supply - amount
        self._balances[frm] = new_balance
        self.total_supply = new_supply
        self.events.append(TransferEvent(frm, ZERO_ADDRESS, amount))

    def transfer(self, frm: str, to: str, amount: UInt256) -> None:
        frm, to = _addr(frm), _addr(to)
        if to == ZERO_ADDRESS:
            raise InvalidAddress("перевод на нулевой адрес (для сжигания есть burn)")
        new_from = self._debit(frm, amount)
        if frm == to:  # перевод самому себе: баланс не меняется, но событие есть (как в ERC-20)
            self.events.append(TransferEvent(frm, to, amount))
            return
        new_to = self.balance_of(to) + amount
        self._balances[frm] = new_from
        self._balances[to] = new_to
        self.events.append(TransferEvent(frm, to, amount))

    def audit(self) -> bool:
        """Инвариант: Σ балансов == total_supply (см. audit_balances)."""
        return audit_balances(self._balances.values(), self.total_supply, self.backend).ok

    def holders(self) -> list[tuple[str, UInt256]]:
        return sorted(((a, b) for a, b in self._balances.items() if b), key=lambda kv: kv[1], reverse=True)

    def fmt(self, value: UInt256) -> str:
        return f"{format_units(value, self.token.decimals)} {self.token.symbol}"

    def _debit(self, frm: str, amount: UInt256) -> UInt256:
        balance = self.balance_of(frm)
        if balance < amount:
            raise InsufficientBalance(f"{frm}: баланс {self.fmt(balance)}, нужно {self.fmt(amount)}")
        return balance - amount
