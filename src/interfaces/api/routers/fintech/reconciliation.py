from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from biz.fintech.reconciliation import Invoice, MatchKind, Payment, Reconciler

from ...errors import BAD_BACKEND
from ...schemas import Backend

router = APIRouter(tags=["fintech/reconciliation"])

Kopecks = Annotated[int, Field(gt=0, description="Сумма в копейках (целое, без float)", examples=[1_250_000])]


class InvoiceIn(BaseModel):
    id: str = Field(description="Номер счёта", examples=["INV-001"])
    customer_id: str = Field(description="Клиент (в реальности — ИНН из выписки)", examples=["7701234567"])
    amount: Kopecks
    due: date = Field(description="Срок оплаты: при нескольких вариантах первыми закрываются старые счета")


class PaymentIn(BaseModel):
    id: str = Field(description="Идентификатор платежа из банковской выписки", examples=["PAY-001"])
    customer_id: str = Field(description="Плательщик", examples=["7701234567"])
    amount: Kopecks


class ReconcileRequest(BaseModel):
    invoices: list[InvoiceIn] = Field(description="Открытые счета (всех клиентов)")
    payments: list[PaymentIn] = Field(description="Входящие платежи, обрабатываются по порядку")
    backend: Backend = None


class MatchOut(BaseModel):
    payment_id: str = Field(description="Платёж")
    kind: Literal["single", "pair", "unmatched"] = Field(
        description="`single` — закрыл один счёт, `pair` — два (Two Sum), `unmatched` — на ручной разбор")
    invoice_ids: list[str] = Field(description="Закрытые счета (пусто для `unmatched`)")


class ReconcileResponse(BaseModel):
    matches: list[MatchOut] = Field(description="Результат по каждому платежу в порядке запроса")
    summary: dict[str, int] = Field(description="Сколько платежей каждого вида", examples=[{"single": 1, "pair": 1, "unmatched": 0}])
    auto_rate: float = Field(description="Доля платежей, сверенных автоматически (0..1)", examples=[0.67])


_EXAMPLES = {
    "pair": {
        "summary": "Один платёж за два счёта",
        "description": "65 000 ₽ = 25 000 + 40 000: платёж закрывает пару счетов.",
        "value": {
            "invoices": [
                {"id": "INV-1", "customer_id": "A", "amount": 1_000_000, "due": "2026-09-01"},
                {"id": "INV-2", "customer_id": "A", "amount": 2_500_000, "due": "2026-09-05"},
                {"id": "INV-3", "customer_id": "A", "amount": 4_000_000, "due": "2026-09-10"},
            ],
            "payments": [{"id": "P-1", "customer_id": "A", "amount": 6_500_000}],
        },
    },
    "mixed": {
        "summary": "Все три исхода",
        "description": "Один счёт, пара счетов и частичная оплата, которая уходит на ручной разбор.",
        "value": {
            "invoices": [
                {"id": "INV-1", "customer_id": "A", "amount": 10_000, "due": "2026-09-01"},
                {"id": "INV-2", "customer_id": "A", "amount": 25_000, "due": "2026-09-05"},
                {"id": "INV-3", "customer_id": "A", "amount": 40_000, "due": "2026-09-10"},
                {"id": "INV-4", "customer_id": "B", "amount": 7_000, "due": "2026-09-01"},
            ],
            "payments": [
                {"id": "P-1", "customer_id": "A", "amount": 65_000},
                {"id": "P-2", "customer_id": "B", "amount": 7_000},
                {"id": "P-3", "customer_id": "A", "amount": 1},
            ],
        },
    },
}


@router.post("/reconcile", summary="Сверить платежи со счетами", responses=BAD_BACKEND)
def reconcile(req: Annotated[ReconcileRequest, Body(openapi_examples=_EXAMPLES)]) -> ReconcileResponse:
    """Сопоставляет каждый платёж с открытыми счетами того же клиента:

    1. платёж = один счёт → закрыть его;
    2. платёж = сумма **двух** счетов → закрыть оба (**LeetCode 1. Two Sum**, `algos.find_pair_with_sum`);
    3. иначе → `unmatched` (частичная оплата, переплата, опечатка).

    Закрытый счёт второй раз не используется. Запрос без состояния: счета и платежи передаются целиком.
    Бизнес-логика: `biz.fintech.reconciliation`.
    """
    rec = Reconciler(backend=req.backend)
    rec.add_invoices(Invoice(**i.model_dump()) for i in req.invoices)
    report = rec.run(Payment(**p.model_dump()) for p in req.payments)
    return ReconcileResponse(
        matches=[
            MatchOut(payment_id=m.payment.id, kind=m.kind.name.lower(), invoice_ids=[i.id for i in m.invoices])
            for m in report.matches
        ],
        summary={k.name.lower(): len(report.by_kind(k)) for k in MatchKind},
        auto_rate=report.auto_rate,
    )
