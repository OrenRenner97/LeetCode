from bisect import bisect_left, insort
from collections import deque
from collections.abc import Iterable
from datetime import datetime

from algos import kth_of_sorted

from .models import FairPrice, FairPriceRule, Status, TradeCheck, VenueReport, VenueState, Verdict


class VenueTape:
    """Сделки одной площадки за скользящее окно, сразу в двух порядках.

    _by_time — очередь по времени: из неё понятно, что пора выкинуть из окна;
    prices   — отсортированный список цен: его и читает бинпоиск, без сортировки на каждый запрос.
    Вставка и удаление — O(n) из-за сдвига списка, но это memmove на C; в проде — дерево порядковых
    статистик или SortedList.
    """

    def __init__(self) -> None:
        self._by_time: deque[tuple[datetime, int]] = deque()
        self.prices: list[int] = []

    def add(self, price: int, ts: datetime) -> None:
        if price <= 0:
            raise ValueError(f"цена должна быть > 0 копеек, получено {price}")
        if self._by_time and ts < self._by_time[-1][0]:
            raise ValueError("сделки площадки должны идти по времени")
        self._by_time.append((ts, price))
        insort(self.prices, price)

    def expire(self, before: datetime) -> None:
        while self._by_time and self._by_time[0][0] < before:
            _, price = self._by_time.popleft()
            del self.prices[bisect_left(self.prices, price)]

    @property
    def last_ts(self) -> datetime | None:
        return self._by_time[-1][0] if self._by_time else None


class FairPricer:
    """Справедливая цена инструмента по нескольким площадкам: медиана всех сделок за окно.

    Почему медиана, а не средняя: одна площадка с ошибкой в фиде (цена ×100) или пара
    «нарисованных» сделок сдвигают среднюю как угодно, а медиану — нет, пока выбросов меньше половины.

    Расчёт (fair_price):
      1. выкинуть сделки старше window, отметить площадки EMPTY и STALE;
      2. живых меньше min_venues → INSUFFICIENT;
      3. первый проход: медиана по всем живым; площадки, чья своя медиана дальше
         max_venue_deviation_bps, — OUTLIER;
      4. без выбросов меньше min_venues → DISPUTED (кто прав — неясно, цену не публикуем);
      5. второй проход по оставшимся: медиана + квартили p25/p75 как коридор.
    Цены у каждой площадки уже отсортированы (VenueTape), поэтому запрос стоит O(V · log n · log R),
    а не O(N log N): справедливую цену можно спрашивать перед каждой сделкой.
    """

    def __init__(self, rule: FairPriceRule | None = None) -> None:
        self.rule = rule or FairPriceRule()
        self._tapes: dict[str, VenueTape] = {}

    def add_trade(self, venue: str, price: int, ts: datetime) -> None:
        self._tapes.setdefault(venue, VenueTape()).add(price, ts)

    def add_trades(self, trades: Iterable[tuple[str, int, datetime]]) -> None:
        for venue, price, ts in trades:
            self.add_trade(venue, price, ts)

    def fair_price(self, now: datetime) -> FairPrice:
        rule = self.rule
        reports: dict[str, VenueReport] = {}
        live: dict[str, list[int]] = {}
        for name, tape in sorted(self._tapes.items()):
            tape.expire(now - rule.window)
            n = len(tape.prices)
            if not n:
                reports[name] = VenueReport(name, VenueState.EMPTY, 0)
            elif tape.last_ts < now - rule.stale_after:
                reports[name] = VenueReport(name, VenueState.STALE, n, _lower_median(tape.prices))
            else:
                live[name] = tape.prices

        if len(live) < rule.min_venues:
            for name, prices in live.items():
                reports[name] = VenueReport(name, VenueState.OK, len(prices), _lower_median(prices))
            return FairPrice(Status.INSUFFICIENT, venues=_ordered(reports))

        first = _median(list(live.values()))
        used: dict[str, list[int]] = {}
        for name, prices in live.items():
            med = _lower_median(prices)
            dev = _bps(med, first)
            if abs(med - first) * 10_000 > rule.max_venue_deviation_bps * first:
                reports[name] = VenueReport(name, VenueState.OUTLIER, len(prices), med, dev)
            else:
                reports[name] = VenueReport(name, VenueState.OK, len(prices), med, dev)
                used[name] = prices

        if len(used) < rule.min_venues:
            return FairPrice(Status.DISPUTED, venues=_ordered(reports))

        arrays = list(used.values())
        total = sum(map(len, arrays))
        return FairPrice(
            Status.OK,
            # Выбросов нет → второй проход совпал бы с первым: экономим 2 из 6 вызовов kth (замер в шаге 3).
            price=first if len(used) == len(live) else _median(arrays),
            p25=kth_of_sorted(*arrays, k=_rank(1, 4, total)),
            p75=kth_of_sorted(*arrays, k=_rank(3, 4, total)),
            trades=total,
            venues=_ordered(reports),
        )

    def check_trade(self, price: int, now: datetime, *, tolerance_bps: int = 200) -> TradeCheck:
        """Контроль нерыночной сделки: цена дальше tolerance_bps от справедливой → OFF_MARKET."""
        fair = self.fair_price(now).price
        return check_against(price, fair, tolerance_bps)


def check_against(price: int, fair: int | None, tolerance_bps: int) -> TradeCheck:
    if fair is None:
        return TradeCheck(price, Verdict.NO_FAIR_PRICE)
    verdict = Verdict.OFF_MARKET if abs(price - fair) * 10_000 > tolerance_bps * fair else Verdict.OK
    return TradeCheck(price, verdict, fair, _bps(price, fair))


def _median(arrays: list[list[int]]) -> int:
    # Медиана в целых копейках: среднее двух средних округляется до чётного (банковское округление),
    # чтобы на длинной дистанции не было систематического сдвига вверх.
    total = sum(map(len, arrays))
    lo = kth_of_sorted(*arrays, k=(total - 1) // 2)
    hi = lo if total % 2 else kth_of_sorted(*arrays, k=total // 2)
    q, r = divmod(lo + hi, 2)
    return q + 1 if r and q % 2 else q


def _lower_median(prices: list[int]) -> int:
    return prices[(len(prices) - 1) // 2]


def _rank(num: int, den: int, total: int) -> int:
    # Перцентиль num/den по nearest-rank: k = ceil(p · N) - 1. Целочисленно, без float.
    return max(0, -(-num * total // den) - 1)


def _bps(price: int, base: int) -> float:
    return round((price - base) * 10_000 / base, 1)


def _ordered(reports: dict[str, VenueReport]) -> tuple[VenueReport, ...]:
    return tuple(reports[name] for name in sorted(reports))
