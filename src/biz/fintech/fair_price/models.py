from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum


def rub(kopecks: int) -> str:
    return f"{kopecks / 100:,.2f} ₽".replace(",", " ")


@dataclass(frozen=True)
class FairPriceRule:
    window: timedelta = timedelta(minutes=5)       # какие сделки участвуют: не старше window
    stale_after: timedelta = timedelta(seconds=30)  # площадка без сделок дольше — фид, скорее всего, завис
    min_venues: int = 2                             # меньше живых площадок — цену не публикуем
    max_venue_deviation_bps: int = 100              # медиана площадки дальше от общей (1% = 100 б.п.) → выброс

    def __post_init__(self):
        if self.min_venues < 1:
            raise ValueError("min_venues должен быть >= 1")
        if self.max_venue_deviation_bps < 0:
            raise ValueError("max_venue_deviation_bps должен быть >= 0")
        if self.window <= timedelta(0) or self.stale_after <= timedelta(0):
            raise ValueError("window и stale_after должны быть > 0")


class Status(Enum):
    OK = "ok"                      # цена посчитана
    INSUFFICIENT = "insufficient"  # живых площадок меньше min_venues
    DISPUTED = "disputed"          # площадки есть, но после отсева выбросов их не хватает: кто прав — неясно


class VenueState(Enum):
    OK = "ok"            # данные в порядке: участвует в цене (если она опубликована)
    EMPTY = "empty"      # сделок в окне нет
    STALE = "stale"      # последняя сделка старше stale_after
    OUTLIER = "outlier"  # медиана площадки слишком далеко от общей


@dataclass(frozen=True)
class VenueReport:
    venue: str
    state: VenueState
    trades: int                # сделок в окне
    median: int | None = None  # нижняя медиана цен площадки
    deviation_bps: float | None = None  # её отклонение от общей цены первого прохода


@dataclass(frozen=True)
class FairPrice:
    status: Status
    price: int | None = None  # медиана в копейках (среднее двух средних — с банковским округлением)
    p25: int | None = None    # коридор: нижний и верхний квартили
    p75: int | None = None
    trades: int = 0           # сколько сделок вошло в расчёт
    venues: tuple[VenueReport, ...] = field(default_factory=tuple)


class Verdict(Enum):
    OK = "ok"
    OFF_MARKET = "off_market"          # отклонение больше допуска → на контроль
    NO_FAIR_PRICE = "no_fair_price"    # сравнить не с чем


@dataclass(frozen=True)
class TradeCheck:
    price: int
    verdict: Verdict
    fair: int | None = None
    deviation_bps: float | None = None
