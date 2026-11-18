from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Action(Enum):
    """Что делать при срабатывании. Порядок — по строгости: при нескольких тревогах побеждает самая строгая."""
    REVIEW = "review"      # отправить аналитику, клиента не трогать
    STEP_UP = "step_up"    # запросить подтверждение (2FA, звонок) перед следующей операцией
    BLOCK = "block"        # остановить операцию и заморозить сессию

    @property
    def severity(self) -> int:
        return {Action.REVIEW: 0, Action.STEP_UP: 1, Action.BLOCK: 2}[self]


class Mode(Enum):
    CONTAINS = "contains"  # сценарий встречается где-то в сессии; срабатывает сразу на последнем событии сценария
    SESSION = "session"    # шаблон описывает ВСЮ сессию целиком; решается при закрытии сессии


@dataclass(frozen=True)
class SessionEvent:
    id: str
    session_id: str
    user_id: str
    ts: datetime
    kind: str            # тип события из каталога: login_new_device, change_phone, payout, …
    amount: int = 0      # копейки, для денежных событий (payout, transfer); у остальных 0


@dataclass(frozen=True)
class Alert:
    rule: str
    action: Action
    session_id: str
    user_id: str
    trigger: SessionEvent     # событие, на котором сценарий сложился (для CONTAINS — его можно ещё остановить)
    started: datetime         # первое событие сессии
    events_seen: int          # событий сессии до триггера включительно
    amount_seen: int          # сумма денежных событий до триггера включительно, копейки
