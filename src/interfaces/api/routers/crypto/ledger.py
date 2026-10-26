"""Крипто-ручки. Все суммы — СТРОКИ: JSON-число в JavaScript точно только до 2^53, а uint256 — до 2^256."""
from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import AfterValidator, BaseModel, Field, model_validator

from biz.crypto.ledger import (
    InsufficientBalance, InvalidAddress, Ledger, Token, UInt256, Uint256Overflow, Uint256Underflow,
    audit_balances, format_units, parse_units,
)

from ...errors import BAD_BACKEND
from ...schemas import Backend

router = APIRouter(tags=["crypto/ledger"])


def _check_uint256(s: str) -> str:
    if int(s) > int(UInt256.MAX):  # ValueError → pydantic отдаст 422
        raise ValueError("больше 2^256 - 1")
    return s


Wei = Annotated[str, Field(pattern=r"^\d{1,78}$", description="uint256 в минимальных единицах (wei), десятичной строкой",
                           examples=["1500000000000000000"]), AfterValidator(_check_uint256)]
Amount = Annotated[str, Field(pattern=r"^(\d+(\.\d*)?|\.\d+)$", description="Сумма в токенах, строкой (float запрещён)",
                              examples=["1.5"])]
Address = Annotated[str, Field(pattern=r"^0x[0-9a-fA-F]{40}$", description="Адрес: `0x` + 40 hex-символов",
                               examples=["0x" + "a1" * 20])]
Decimals = Annotated[int, Field(ge=0, le=77, description="Знаков после точки: ETH = 18, USDT/USDC = 6, BTC = 8", examples=[18])]


class TokenIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=11, description="Тикер", examples=["ETH"])
    decimals: Decimals


class Operation(BaseModel):
    op: Literal["mint", "burn", "transfer"] = Field(description="`mint` — выпуск, `burn` — сжигание, `transfer` — перевод")
    from_: Address | None = Field(None, alias="from", description="Отправитель (`burn`, `transfer`)")
    to: Address | None = Field(None, description="Получатель (`mint`, `transfer`)")
    amount: Amount

    @model_validator(mode="after")
    def _fields_for_op(self):
        need = {"mint": ("to",), "burn": ("from_",), "transfer": ("from_", "to")}[self.op]
        missing = [n.rstrip("_") for n in need if getattr(self, n) is None]
        if missing:
            raise ValueError(f"для {self.op} нужны поля: {', '.join(missing)}")
        return self


class SimulateRequest(BaseModel):
    token: TokenIn
    operations: list[Operation] = Field(max_length=10_000, description="Операции, применяются по порядку")
    backend: Backend = None


class TokenAmount(BaseModel):
    amount: str = Field(description="В токенах", examples=["7.5"])
    wei: str = Field(description="В минимальных единицах", examples=["7500000000000000000"])


class BalanceOut(TokenAmount):
    address: str = Field(description="Адрес держателя")


class EventOut(TokenAmount):
    from_: str = Field(alias="from", description="Отправитель (`0x000…0` для mint)")
    to: str = Field(description="Получатель (`0x000…0` для burn)")


class FailedOp(BaseModel):
    index: int = Field(description="Номер операции в запросе (с 0)")
    error: str = Field(description="Тип ошибки", examples=["InsufficientBalance"])
    message: str = Field(description="Подробности")


class SimulateResponse(BaseModel):
    balances: list[BalanceOut] = Field(description="Ненулевые балансы, по убыванию")
    total_supply: TokenAmount
    events: list[EventOut] = Field(description="Журнал Transfer-событий (как в ERC-20)")
    failed: list[FailedOp] = Field(description="Откаченные операции (как `revert` в EVM): состояние не изменилось")
    audit_ok: bool = Field(description="Инвариант Σ балансов == total_supply")


_SIM_EXAMPLES = {
    "basic": {
        "summary": "Выпуск, перевод и ошибка",
        "description": "Третья операция откатывается: у bob всего 1 wei.",
        "value": {
            "token": {"symbol": "ETH", "decimals": 18},
            "operations": [
                {"op": "mint", "to": "0x" + "a1" * 20, "amount": "10"},
                {"op": "mint", "to": "0x" + "b0" * 20, "amount": "0.000000000000000001"},
                {"op": "transfer", "from": "0x" + "b0" * 20, "to": "0x" + "a1" * 20, "amount": "1"},
                {"op": "transfer", "from": "0x" + "a1" * 20, "to": "0x" + "c4" * 20, "amount": "2.5"},
            ],
        },
    },
}


@router.post("/ledger/simulate", summary="Прогнать операции ERC-20 на uint256", responses=BAD_BACKEND)
def simulate_ledger(req: Annotated[SimulateRequest, Body(openapi_examples=_SIM_EXAMPLES)]) -> SimulateResponse:
    """Применяет `mint` / `burn` / `transfer` к пустому реестру токена и возвращает итог.

    Арифметика как в EVM: **uint256** = 4 лимба по 64 бита (**LeetCode 2. Add Two Numbers**,
    `algos.add_digits` / `sub_digits`). Переполнение, нехватка баланса или нулевой адрес откатывают
    операцию (она попадает в `failed`), остальные продолжаются. Бизнес-логика: `biz.crypto.ledger`.
    """
    led = Ledger(Token(req.token.symbol, req.token.decimals), backend=req.backend)
    failed = []
    for k, op in enumerate(req.operations):
        try:
            amount = parse_units(op.amount, led.token.decimals)
            if op.op == "mint":
                led.mint(op.to, amount)
            elif op.op == "burn":
                led.burn(op.from_, amount)
            else:
                led.transfer(op.from_, op.to, amount)
        except (InsufficientBalance, InvalidAddress, Uint256Overflow, Uint256Underflow, ValueError) as e:
            failed.append(FailedOp(index=k, error=type(e).__name__, message=str(e)))

    def amt(v: UInt256) -> dict:
        return {"amount": format_units(v, led.token.decimals), "wei": str(int(v))}

    return SimulateResponse(
        balances=[BalanceOut(address=a, **amt(b)) for a, b in led.holders()],
        total_supply=TokenAmount(**amt(led.total_supply)),
        events=[EventOut(**{"from": e.frm}, to=e.to, **amt(e.value)) for e in led.events],
        failed=failed,
        audit_ok=led.audit(),
    )


class AuditRequest(BaseModel):
    balances: list[Wei] = Field(max_length=1_000_000, description="Балансы всех держателей (снимок)")
    total_supply: Wei
    backend: Backend = None


class AuditResponse(BaseModel):
    ok: bool = Field(description="Σ балансов == total_supply")
    balances_sum: str = Field(description="Σ балансов (может превышать 2^256, если данные испорчены)")
    total_supply: str = Field(description="Заявленный выпуск")
    difference: str = Field(description="Σ балансов − total_supply (со знаком; `0`, если всё сходится)")
    holders: int = Field(description="Сколько балансов проверено")


_AUDIT_EXAMPLES = {
    "ok": {"summary": "Всё сходится", "value": {"balances": ["7500000000000000000", "2500000000000000000"],
                                                 "total_supply": "10000000000000000000"}},
    "mismatch": {"summary": "Недостача 1 wei", "value": {"balances": ["7500000000000000000", "2499999999999999999"],
                                                           "total_supply": "10000000000000000000"}},
}


@router.post("/ledger/audit", summary="Аудит: Σ балансов == total_supply", responses=BAD_BACKEND)
def audit_ledger(req: Annotated[AuditRequest, Body(openapi_examples=_AUDIT_EXAMPLES)]) -> AuditResponse:
    """Сверяет снимок балансов с заявленным выпуском токена, например после индексации блокчейна.

    Балансы не складываются по одному: столбцы лимбов суммируются разом, а переносы разрешаются в конце
    (**carry-save**, `algos.sum_limbs`). На 10⁵ держателей это ~4000× быстрее наивного цикла, на 10⁷ — ~40 ms (numba).
    """
    res = audit_balances((UInt256(int(b)) for b in req.balances), UInt256(int(req.total_supply)), req.backend)
    return AuditResponse(ok=res.ok, balances_sum=str(res.balances_sum), total_supply=str(int(res.total_supply)),
                         difference=str(res.balances_sum - int(res.total_supply)), holders=res.holders)


class UnitsOut(BaseModel):
    amount: str = Field(description="В токенах", examples=["1.5"])
    wei: str = Field(description="В минимальных единицах", examples=["1500000000000000000"])
    decimals: int = Field(description="Знаков после точки", examples=[18])


@router.get("/units/parse", summary="Токены → wei")
def parse_amount(amount: Annotated[Amount, Query()], decimals: Annotated[Decimals, Query()] = 18) -> UnitsOut:
    """`1.5` при `decimals=18` → `1500000000000000000`. Без float: точно до последнего wei. 422, если знаков больше, чем decimals."""
    try:
        wei = parse_units(amount, decimals)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    return UnitsOut(amount=format_units(wei, decimals), wei=str(int(wei)), decimals=decimals)


@router.get("/units/format", summary="wei → токены")
def format_amount(wei: Annotated[Wei, Query()], decimals: Annotated[Decimals, Query()] = 18) -> UnitsOut:
    """`1500000000000000000` при `decimals=18` → `1.5`. Разделитель тысяч — `_`."""
    return UnitsOut(amount=format_units(UInt256(int(wei)), decimals), wei=wei, decimals=decimals)
