from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Status(Enum):
    APPROVED = "approved"
    DECLINED = "declined"


@dataclass(frozen=True)
class PaymentAttempt:
    id: str
    ts: datetime
    source: str       # IP или отпечаток устройства: «откуда» платят
    card_fp: str      # отпечаток карты (хэш PAN с солью). Сам номер карты сюда не попадает: PCI DSS
    card_last4: str   # для человека в отчёте
    amount: int       # в копейках
    status: Status


class Risk(Enum):
    HIGH = "high"      # много разных карт подряд И много отказов: почти наверняка перебор украденных карт
    MEDIUM = "medium"  # много разных карт подряд, но отказов мало: семья, офис, кафе с общим Wi-Fi или аккуратный мошенник


@dataclass(frozen=True)
class Alert:
    source: str
    risk: Risk
    attempts: tuple[PaymentAttempt, ...]  # подряд идущие попытки самого длинного подозрительного окна

    @property
    def distinct_cards(self) -> int:
        return len({a.card_fp for a in self.attempts})

    @property
    def declines(self) -> int:
        return sum(a.status is Status.DECLINED for a in self.attempts)

    @property
    def decline_rate(self) -> float:
        return self.declines / len(self.attempts)

    @property
    def total_amount(self) -> int:
        return sum(a.amount for a in self.attempts)

    @property
    def start(self) -> datetime:
        return self.attempts[0].ts

    @property
    def end(self) -> datetime:
        return self.attempts[-1].ts

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def action(self) -> str:
        return "block" if self.risk is Risk.HIGH else "review"
