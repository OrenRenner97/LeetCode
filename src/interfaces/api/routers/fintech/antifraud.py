import re
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import AfterValidator, BaseModel, Field

from biz.fintech.antifraud import CardTestingDetector, CardTestingRule, PaymentAttempt, Status

from ...errors import BAD_BACKEND
from ...schemas import Backend

router = APIRouter(prefix="/antifraud", tags=["fintech/antifraud"])

_LOOKS_LIKE_PAN = re.compile(r"^\d{13,19}$")


def _not_a_pan(v: str) -> str:
    if _LOOKS_LIKE_PAN.match(v.replace(" ", "")):
        raise ValueError("похоже на номер карты: передавайте отпечаток (хэш с солью), а не PAN (PCI DSS)")
    return v


class AttemptIn(BaseModel):
    id: str = Field(description="Идентификатор попытки оплаты", examples=["A-0001"])
    ts: datetime = Field(description="Время попытки: окно строится по порядку времени внутри источника")
    source: str = Field(description="Откуда платят: IP или отпечаток устройства", examples=["203.0.113.7"])
    card_fp: Annotated[str, Field(min_length=8, max_length=128, examples=["9f2c1a7e4b8d0c33"],
                                  description="Отпечаток карты (хэш PAN с солью). Сам номер карты слать нельзя: вернётся 422"),
                       AfterValidator(_not_a_pan)]
    card_last4: str = Field(pattern=r"^\d{4}$", description="Последние 4 цифры, для человека в отчёте", examples=["4242"])
    amount: int = Field(ge=0, description="Сумма в копейках", examples=[100])
    status: Literal["approved", "declined"] = Field(description="Ответ банка-эмитента")


class RuleIn(BaseModel):
    min_cards: int = Field(5, ge=2, description="От скольких разных карт подряд поднимать тревогу")
    max_repeats: int = Field(1, ge=1, description="Сколько раз одна карта может встретиться в окне; "
                                                  "2+ ловит обход «каждую карту по два раза»")
    high_decline_rate: float = Field(0.5, ge=0, le=1, description="Доля отказов в окне, с которой риск `high` (→ `block`)")


class CardTestingRequest(BaseModel):
    attempts: list[AttemptIn] = Field(max_length=100_000, description="Попытки оплаты в любом порядке, из любых источников")
    rule: RuleIn = Field(default_factory=RuleIn, description="Параметры правила (все необязательные)")
    backend: Backend = None


class AlertOut(BaseModel):
    source: str = Field(description="Подозрительный источник")
    risk: Literal["high", "medium"] = Field(description="`high` — много карт и много отказов; `medium` — много карт, отказов мало")
    action: Literal["block", "review"] = Field(description="Рекомендация: `block` для high, `review` (ручной разбор) для medium")
    distinct_cards: int = Field(description="Разных карт в окне")
    attempts: int = Field(description="Попыток в окне")
    declines: int = Field(description="Отказов в окне")
    decline_rate: float = Field(description="Доля отказов (0..1)")
    total_amount: int = Field(description="Сумма попыток в окне, копейки")
    start: datetime = Field(description="Первая попытка окна")
    end: datetime = Field(description="Последняя попытка окна")
    duration_seconds: float = Field(description="Длительность окна")
    attempt_ids: list[str] = Field(description="Попытки окна по порядку: для расследования")


class CardTestingResponse(BaseModel):
    alerts: list[AlertOut] = Field(description="Тревоги: сначала `high`, затем по числу карт")
    scanned_attempts: int = Field(description="Сколько попыток проверено")
    scanned_sources: int = Field(description="Сколько разных источников")


def _ex_attempt(k, source, card, status, minute):
    return {"id": f"A-{k}", "ts": f"2026-10-24T12:{minute:02d}:00Z", "source": source,
            "card_fp": f"fp{card:014x}", "card_last4": f"{card % 10000:04d}", "amount": 100, "status": status}


_EXAMPLES = {
    "card_testing": {
        "summary": "Перебор украденных карт",
        "description": "Шесть разных карт подряд по 1 ₽ с одного IP, почти все отклонены → `high` / `block`.",
        "value": {"attempts": [_ex_attempt(k, "203.0.113.7", 1000 + k, "approved" if k == 4 else "declined", k)
                               for k in range(6)]},
    },
    "evasion": {
        "summary": "Обход: каждая карта дважды",
        "description": "Со строгим правилом тревоги нет. С `max_repeats: 2` окно ловится.",
        "value": {"attempts": [_ex_attempt(k, "198.51.100.9", 2000 + k // 2, "declined", k) for k in range(12)],
                  "rule": {"max_repeats": 2}},
    },
}


@router.post("/card-testing", summary="Найти перебор украденных карт", responses=BAD_BACKEND)
def detect_card_testing(req: Annotated[CardTestingRequest, Body(openapi_examples=_EXAMPLES)]) -> CardTestingResponse:
    """Card testing: мошенник с одного источника пробует подряд много **разных** карт мелкими платежами.

    Для каждого источника ищется самое длинное окно подряд идущих попыток, где каждая карта встречается
    не больше `max_repeats` раз (**LeetCode 3. Longest Substring Without Repeating Characters**,
    `algos.longest_unique_window`). Если разных карт в окне ≥ `min_cards` — тревога.
    Бизнес-логика: `biz.fintech.antifraud`.
    """
    rule = CardTestingRule(**req.rule.model_dump())
    attempts = [PaymentAttempt(**{**a.model_dump(), "status": Status(a.status)}) for a in req.attempts]
    alerts = CardTestingDetector(rule, backend=req.backend).scan(attempts)
    return CardTestingResponse(
        alerts=[
            AlertOut(source=al.source, risk=al.risk.value, action=al.action, distinct_cards=al.distinct_cards,
                     attempts=len(al.attempts), declines=al.declines, decline_rate=al.decline_rate,
                     total_amount=al.total_amount, start=al.start, end=al.end,
                     duration_seconds=al.duration.total_seconds(), attempt_ids=[a.id for a in al.attempts])
            for al in alerts
        ],
        scanned_attempts=len(attempts),
        scanned_sources=len({a.source for a in attempts}),
    )
