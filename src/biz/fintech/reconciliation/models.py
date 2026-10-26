from dataclasses import dataclass, field
from datetime import date
from enum import Enum


def rub(kopecks: int) -> str:
    return f"{kopecks / 100:,.2f} ₽".replace(",", " ")


@dataclass(frozen=True)
class Invoice:
    id: str
    customer_id: str
    amount: int  # в копейках: деньги не храним во float, иначе 0.1 + 0.2 != 0.3
    due: date


@dataclass(frozen=True)
class Payment:
    id: str
    customer_id: str  # в реальности определяется по ИНН / счёту плательщика из выписки
    amount: int


class MatchKind(Enum):
    SINGLE = "одним счётом"
    PAIR = "парой счетов"
    UNMATCHED = "на ручной разбор"


@dataclass(frozen=True)
class Match:
    payment: Payment
    kind: MatchKind
    invoices: tuple[Invoice, ...] = ()


@dataclass
class Report:
    matches: list[Match] = field(default_factory=list)

    def by_kind(self, kind: MatchKind) -> list[Match]:
        return [m for m in self.matches if m.kind is kind]

    @property
    def auto_rate(self) -> float:
        if not self.matches:
            return 0.0
        return 1 - len(self.by_kind(MatchKind.UNMATCHED)) / len(self.matches)
