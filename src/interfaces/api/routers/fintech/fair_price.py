from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import AwareDatetime, BaseModel, Field

from biz.fintech.fair_price import FairPriceRule, FairPricer, check_against

router = APIRouter(tags=["fintech/fair_price"])

Kopecks = Annotated[int, Field(gt=0, description="Цена за единицу в копейках (целое, без float)", examples=[28_543])]


class TradeIn(BaseModel):
    venue: str = Field(description="Площадка: биржа, ОТС, брокер", examples=["Биржа A"])
    price: Kopecks
    ts: AwareDatetime = Field(description="Время сделки с часовым поясом. Порядок в запросе не важен: сортируем сами")


class RuleIn(BaseModel):
    window_s: int = Field(300, gt=0, description="Окно в секундах: участвуют сделки не старше")
    stale_after_s: int = Field(30, gt=0, description="Площадка без сделок дольше — фид завис, её не учитываем")
    min_venues: int = Field(2, ge=1, description="Меньше живых площадок — цену не публикуем")
    max_venue_deviation_bps: int = Field(
        100, ge=0, description="Медиана площадки дальше от общей (в б.п., 100 = 1%) → площадка-выброс")


class FairPriceRequest(BaseModel):
    now: AwareDatetime = Field(description="Момент расчёта: от него отсчитываются окно и «зависание» фидов")
    trades: list[TradeIn] = Field(description="Сделки по всем площадкам")
    rule: RuleIn = Field(default_factory=RuleIn, description="Параметры расчёта")
    check_prices: list[Kopecks] = Field(
        default_factory=list, description="Цены своих сделок для контроля нерыночности (необязательно)")
    tolerance_bps: int = Field(200, ge=0, description="Допуск для check_prices в б.п. (200 = 2%)")


class VenueOut(BaseModel):
    venue: str = Field(description="Площадка")
    state: Literal["ok", "empty", "stale", "outlier"] = Field(
        description="`ok` — данные в порядке, `empty` — нет сделок в окне, `stale` — фид завис, "
                    "`outlier` — медиана площадки слишком далеко от общей")
    trades: int = Field(description="Сделок площадки в окне")
    median: int | None = Field(description="Нижняя медиана цен площадки, копейки")
    deviation_bps: float | None = Field(description="Отклонение медианы площадки от общей цены первого прохода, б.п.")


class CheckOut(BaseModel):
    price: int = Field(description="Проверяемая цена, копейки")
    verdict: Literal["ok", "off_market", "no_fair_price"] = Field(
        description="`off_market` — отклонение больше допуска, `no_fair_price` — цена не опубликована, сравнить не с чем")
    deviation_bps: float | None = Field(description="Отклонение от справедливой цены, б.п.")


class FairPriceResponse(BaseModel):
    status: Literal["ok", "insufficient", "disputed"] = Field(
        description="`insufficient` — мало живых площадок, `disputed` — после отсева выбросов площадок не хватает")
    price: int | None = Field(description="Справедливая цена (медиана всех сделок), копейки")
    p25: int | None = Field(description="Нижний квартиль: нижняя граница коридора")
    p75: int | None = Field(description="Верхний квартиль: верхняя граница коридора")
    trades: int = Field(description="Сколько сделок вошло в расчёт")
    venues: list[VenueOut] = Field(description="Состояние каждой площадки")
    checks: list[CheckOut] = Field(description="Результаты по check_prices в том же порядке")


_T = "2026-10-27T12:00:{:02d}+03:00"
_EXAMPLES = {
    "normal": {
        "summary": "Три площадки, одна своя сделка подозрительная",
        "description": "Медиана по всем сделкам; сделка по 294.00 ₽ дальше 2% от справедливой цены → `off_market`.",
        "value": {
            "now": _T.format(59),
            "trades": [
                {"venue": "Биржа A", "price": 28_540, "ts": _T.format(10)},
                {"venue": "Биржа A", "price": 28_545, "ts": _T.format(40)},
                {"venue": "Биржа B", "price": 28_548, "ts": _T.format(30)},
                {"venue": "Биржа B", "price": 28_541, "ts": _T.format(50)},
                {"venue": "ОТС", "price": 28_536, "ts": _T.format(45)},
            ],
            "check_prices": [28_560, 29_400],
        },
    },
    "broken_feed": {
        "summary": "Сбой фида на одной площадке",
        "description": "Брокер X шлёт цены ×100. Средняя улетела бы в 10 раз, медиана — нет, а площадка помечается `outlier`.",
        "value": {
            "now": _T.format(59),
            "trades": [
                {"venue": "Биржа A", "price": 28_540, "ts": _T.format(10)},
                {"venue": "Биржа A", "price": 28_545, "ts": _T.format(40)},
                {"venue": "Биржа B", "price": 28_541, "ts": _T.format(50)},
                {"venue": "Брокер X", "price": 2_854_300, "ts": _T.format(55)},
            ],
        },
    },
}


@router.post("/fair-price", summary="Справедливая цена по нескольким площадкам")
def fair_price(req: Annotated[FairPriceRequest, Body(openapi_examples=_EXAMPLES)]) -> FairPriceResponse:
    """Медиана цен всех сделок за окно по всем живым площадкам и коридор p25–p75.

    Площадки без сделок, с зависшим фидом и с ценами далеко от остальных из расчёта исключаются и
    видны в `venues`. Медиана и квартили — k-й элемент объединения отсортированных лент сделок без
    их слияния (**LeetCode 4. Median of Two Sorted Arrays**, `algos.kth_of_sorted`).
    Дополнительно проверяет свои сделки (`check_prices`) на нерыночность.
    Бизнес-логика: `biz.fintech.fair_price`.
    """
    r = req.rule
    pricer = FairPricer(FairPriceRule(
        window=timedelta(seconds=r.window_s),
        stale_after=timedelta(seconds=r.stale_after_s),
        min_venues=r.min_venues,
        max_venue_deviation_bps=r.max_venue_deviation_bps,
    ))
    pricer.add_trades((t.venue, t.price, t.ts) for t in sorted(req.trades, key=lambda t: t.ts))
    fp = pricer.fair_price(req.now)
    return FairPriceResponse(
        status=fp.status.value,
        price=fp.price,
        p25=fp.p25,
        p75=fp.p75,
        trades=fp.trades,
        venues=[VenueOut(venue=v.venue, state=v.state.value, trades=v.trades, median=v.median,
                         deviation_bps=v.deviation_bps) for v in fp.venues],
        checks=[CheckOut(price=c.price, verdict=c.verdict.value, deviation_bps=c.deviation_bps)
                for c in (check_against(p, fp.price, req.tolerance_bps) for p in req.check_prices)],
    )
