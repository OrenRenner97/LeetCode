import random
import statistics
from datetime import datetime, timedelta

import pytest

from biz.fintech.fair_price import (
    FairPriceRule,
    FairPricer,
    Status,
    VenueState,
    VenueTape,
    Verdict,
    check_against,
)

NOW = datetime(2026, 10, 27, 12, 0, 0)


def _ago(seconds):
    return NOW - timedelta(seconds=seconds)


def _pricer(venues, rule=None):
    # venues: {площадка: [(цена, секунд назад), ...]} — порядок по времени выставляем сами.
    p = FairPricer(rule)
    for venue, trades in venues.items():
        for price, age in sorted(trades, key=lambda t: -t[1]):
            p.add_trade(venue, price, _ago(age))
    return p


def _states(fp):
    return {v.venue: v.state for v in fp.venues}


def test_median_over_all_venues():
    fp = _pricer({"A": [(100, 5), (102, 4), (104, 3)], "B": [(101, 2), (103, 1)]}).fair_price(NOW)
    assert fp.status is Status.OK
    assert fp.price == 102 and fp.trades == 5
    assert (fp.p25, fp.p75) == (101, 103)


def test_even_count_rounds_half_to_even():
    # (100 + 101) / 2 = 100.5 → 100 (чётное), (101 + 102) / 2 = 101.5 → 102.
    assert _pricer({"A": [(100, 2)], "B": [(101, 1)]}).fair_price(NOW).price == 100
    assert _pricer({"A": [(101, 2)], "B": [(102, 1)]}).fair_price(NOW).price == 102


def test_insufficient_venues():
    fp = _pricer({"A": [(100, 1)]}).fair_price(NOW)
    assert fp.status is Status.INSUFFICIENT and fp.price is None
    assert _states(fp) == {"A": VenueState.OK}
    assert FairPricer().fair_price(NOW).status is Status.INSUFFICIENT


def test_window_expires_old_trades():
    rule = FairPriceRule(window=timedelta(minutes=1), stale_after=timedelta(minutes=1))
    p = _pricer({"A": [(500, 120), (100, 10)], "B": [(100, 5)]}, rule)
    fp = p.fair_price(NOW)
    assert fp.price == 100 and fp.trades == 2  # сделка 2 минуты назад выпала из окна


def test_empty_and_stale_venues_excluded():
    rule = FairPriceRule(window=timedelta(minutes=5), stale_after=timedelta(seconds=30))
    p = _pricer({"A": [(100, 1)], "B": [(101, 2)], "C": [(900, 60)], "D": [(900, 600)]}, rule)
    fp = p.fair_price(NOW)
    assert _states(fp) == {"A": VenueState.OK, "B": VenueState.OK, "C": VenueState.STALE, "D": VenueState.EMPTY}
    assert fp.price == 100


def test_outlier_venue_dropped():
    # Брокер шлёт цены ×100 (копейки вместо рублей): медиана устойчива, а площадка отмечается.
    venues = {"A": [(28_540, 3), (28_545, 2)], "B": [(28_541, 2), (28_543, 1)], "X": [(2_854_000, 1)]}
    fp = _pricer(venues).fair_price(NOW)
    assert fp.status is Status.OK
    assert _states(fp)["X"] is VenueState.OUTLIER
    assert fp.price == 28_542 and fp.trades == 4


def test_two_disagreeing_venues_disputed():
    fp = _pricer({"A": [(10_000, 1)], "B": [(10_300, 1)]}).fair_price(NOW)
    assert fp.status is Status.DISPUTED and fp.price is None
    assert set(_states(fp).values()) == {VenueState.OUTLIER}


def test_check_trade():
    p = _pricer({"A": [(10_000, 2)], "B": [(10_000, 1)]})
    assert p.check_trade(10_150, NOW).verdict is Verdict.OK              # +150 б.п. при допуске 200
    off = p.check_trade(10_250, NOW)
    assert off.verdict is Verdict.OFF_MARKET and off.deviation_bps == 250.0
    assert p.check_trade(10_250, NOW, tolerance_bps=300).verdict is Verdict.OK
    assert check_against(10_000, None, 200).verdict is Verdict.NO_FAIR_PRICE


def test_tolerance_boundary_is_inclusive():
    assert check_against(10_200, 10_000, 200).verdict is Verdict.OK      # ровно на границе — ещё рыночная
    assert check_against(10_201, 10_000, 200).verdict is Verdict.OFF_MARKET


def test_random_against_statistics():
    rng = random.Random(1)
    rule = FairPriceRule(max_venue_deviation_bps=10**9)  # отсев выбросов выключен: сверяем чистую медиану
    for _ in range(300):
        venues = {f"V{i}": [(rng.randint(1, 50), rng.randint(0, 20)) for _ in range(rng.randint(1, 8))]
                  for i in range(rng.randint(2, 5))}
        fp = _pricer(venues, rule).fair_price(NOW)
        prices = sorted(p for trades in venues.values() for p, _ in trades)
        assert fp.price == round(statistics.median(prices))  # round() в Python — тоже до чётного
        assert fp.p25 == prices[-(-len(prices) // 4) - 1]


def test_tape_validation():
    t = VenueTape()
    with pytest.raises(ValueError):
        t.add(0, NOW)
    t.add(100, NOW)
    with pytest.raises(ValueError):
        t.add(100, _ago(1))  # назад во времени


def test_rule_validation():
    with pytest.raises(ValueError):
        FairPriceRule(min_venues=0)
    with pytest.raises(ValueError):
        FairPriceRule(window=timedelta(0))
