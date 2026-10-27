"""Демо: python -m biz.fintech.fair_price.demo"""
import random
from datetime import datetime, timedelta

from .models import FairPrice, FairPriceRule, Status, rub
from .pricer import FairPricer

NOW = datetime(2026, 10, 27, 12, 0, 0)


def tape(rng: random.Random, center: int, n: int, spread: int, last_age_s: int = 0):
    """n сделок вокруг center (копейки) за последние 5 минут; последняя — last_age_s секунд назад."""
    times = sorted(NOW - timedelta(seconds=last_age_s + rng.uniform(0, 290)) for _ in range(n - 1))
    times.append(NOW - timedelta(seconds=last_age_s))
    return [(max(1, center + rng.randint(-spread, spread)), ts) for ts in times]


def show(title: str, pricer: FairPricer, mean_of: list[int]) -> FairPrice:
    fp = pricer.fair_price(NOW)
    print(f"\n== {title}")
    for v in fp.venues:
        med = rub(v.median) if v.median else "—"
        dev = f"{round(v.deviation_bps):+d} б.п." if v.deviation_bps is not None else ""
        print(f"  {v.venue:<12} {v.state.value:<8} сделок {v.trades:>4}   медиана {med:>12}  {dev}")
    if fp.status is Status.OK:
        print(f"  справедливая цена: {rub(fp.price)}  (коридор p25–p75: {rub(fp.p25)} – {rub(fp.p75)}, сделок {fp.trades})")
    else:
        print(f"  цена не публикуется: {fp.status.value}")
    print(f"  для сравнения, средняя по всем сделкам: {rub(round(sum(mean_of) / len(mean_of)))}")
    return fp


def scenario(name: str, venues: dict[str, list], rule: FairPriceRule | None = None) -> FairPricer:
    pricer = FairPricer(rule)
    for venue, trades in venues.items():
        for price, ts in trades:
            pricer.add_trade(venue, price, ts)
    show(name, pricer, [p for trades in venues.values() for p, _ in trades])
    return pricer


def main() -> None:
    rng = random.Random(4)
    base = 28_543  # 285.43 ₽ за акцию

    pricer = scenario("Обычный рынок: три площадки", {
        "Биржа A": tape(rng, base, 400, 15),
        "Биржа B": tape(rng, base + 3, 120, 20),
        "ОТС": tape(rng, base - 2, 30, 25),
    })
    for price in (28_560, 29_400):
        c = pricer.check_trade(price, NOW)
        print(f"  проверка сделки по {rub(price)}: {c.verdict.value} ({round(c.deviation_bps):+d} б.п.)")

    scenario("Сбой фида: площадка шлёт цену в копейках вместо рублей ×100", {
        "Биржа A": tape(rng, base, 400, 15),
        "Биржа B": tape(rng, base + 3, 120, 20),
        "Брокер X": tape(rng, base * 100, 50, 1500),
    })

    scenario("Завис фид: последняя сделка на Бирже B 2 минуты назад", {
        "Биржа A": tape(rng, base, 400, 15),
        "Биржа B": tape(rng, base + 3, 120, 20, last_age_s=120),
        "ОТС": tape(rng, base - 2, 30, 25),
    })

    scenario("Две площадки расходятся на 3%: кто прав — неизвестно", {
        "Биржа A": tape(rng, base, 200, 15),
        "ОТС": tape(rng, base * 103 // 100, 200, 15),
    })


if __name__ == "__main__":
    main()
