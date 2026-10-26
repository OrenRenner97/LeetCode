"""Демо: python -m biz.fintech.antifraud.demo"""
import hashlib
import random
from datetime import datetime, timedelta

from .detector import CardTestingDetector, CardTestingRule
from .models import PaymentAttempt, Status


def card(pan: str) -> tuple[str, str]:
    # Отпечаток карты: хэш номера с солью. Детектору номер не нужен, только «та же карта или другая».
    return hashlib.sha256(b"demo-salt:" + pan.encode()).hexdigest()[:16], pan[-4:]


def generate(seed: int = 3) -> list[PaymentAttempt]:
    rng = random.Random(seed)
    t0 = datetime(2026, 10, 24, 12, 0)
    out: list[PaymentAttempt] = []

    def add(source, pan, amount, ok, minute):
        fp, last4 = card(pan)
        out.append(PaymentAttempt(f"A{len(out):04d}", t0 + timedelta(minutes=minute), source, fp, last4,
                                  amount, Status.APPROVED if ok else Status.DECLINED))

    stolen = [f"4000{rng.randrange(10**12):012d}" for _ in range(40)]

    # Обычные покупатели: 1–2 своих карты, иногда отказ.
    for u in range(30):
        cards = [f"5500{rng.randrange(10**12):012d}" for _ in range(rng.choice([1, 1, 2]))]
        for k in range(rng.randint(1, 6)):
            add(f"user-{u:02d}", rng.choice(cards), rng.randrange(500, 20_000) * 100, rng.random() > 0.05, rng.randrange(600))

    # Семья / офис за одним IP: 5 разных карт, все платежи проходят → MEDIUM (на ручной разбор, не блок).
    for k, pan in enumerate(f"2200{rng.randrange(10**12):012d}" for _ in range(5)):
        add("office-nat", pan, rng.randrange(300, 3000) * 100, True, 100 + k * 40)

    # Мошенник 1: 20 украденных карт подряд по 1 ₽, большинство отклонено → HIGH.
    for k, pan in enumerate(stolen[:20]):
        add("fraud-ip-1", pan, 100, rng.random() < 0.15, 300 + k * 0.2)

    # Мошенник 2 «хитрый»: каждую карту пробует дважды — строгое правило (max_repeats=1) видит окна по 2 карты.
    for k, pan in enumerate(stolen[20:32]):
        for rep in range(2):
            add("fraud-ip-2", pan, 100, rng.random() < 0.15, 400 + k * 0.5 + rep * 0.1)

    rng.shuffle(out)  # в реальности события приходят вперемешку
    return out


def show(title, alerts):
    print(f"\n== {title}: тревог {len(alerts)}")
    for al in alerts:
        print(f"  [{al.risk.value:<6} → {al.action:<6}] {al.source:<11} карт подряд: {al.distinct_cards:>2}  "
              f"попыток: {len(al.attempts):>2}  отказов: {al.decline_rate:4.0%}  "
              f"сумма: {al.total_amount / 100:>9,.2f} ₽  за {al.duration}")


def main() -> None:
    attempts = generate()
    print(f"Попыток: {len(attempts)}, источников: {len({a.source for a in attempts})}")
    show("строгое правило (каждая карта ≤ 1 раза в окне)", CardTestingDetector(CardTestingRule(min_cards=5)).scan(attempts))
    show("против обхода (каждая карта ≤ 2 раз в окне)", CardTestingDetector(CardTestingRule(min_cards=5, max_repeats=2)).scan(attempts))


if __name__ == "__main__":
    main()
