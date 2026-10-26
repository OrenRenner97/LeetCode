"""Демо: python -m biz.fintech.reconciliation.demo [--backend python]"""
import argparse
import random
from datetime import date, timedelta

from .models import Invoice, MatchKind, Payment, rub
from .reconciler import Reconciler


def generate(seed: int = 7, customers: int = 4, invoices_per_customer: int = 6):
    rng = random.Random(seed)
    invoices, payments = [], []
    start = date(2026, 9, 1)
    pid = 0

    for c in range(1, customers + 1):
        cid = f"ООО Клиент-{c}"
        own = [
            Invoice(
                id=f"INV-{c}{k:02d}",
                customer_id=cid,
                amount=rng.randrange(5_000, 500_000) * 100,
                due=start + timedelta(days=rng.randrange(0, 45)),
            )
            for k in range(1, invoices_per_customer + 1)
        ]
        invoices += own
        rng.shuffle(own)

        # Сценарии оплаты: один счёт, два счёта одним платежом, частичная оплата.
        pid += 1
        payments.append(Payment(f"PAY-{pid:03d}", cid, own[0].amount))
        pid += 1
        payments.append(Payment(f"PAY-{pid:03d}", cid, own[1].amount + own[2].amount))
        pid += 1
        payments.append(Payment(f"PAY-{pid:03d}", cid, own[3].amount // 2))

    rng.shuffle(payments)
    return invoices, payments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=None, help="python | numba | c | cuda (по умолчанию auto)")
    args = parser.parse_args()

    invoices, payments = generate()
    rec = Reconciler(backend=args.backend)
    rec.add_invoices(invoices)
    report = rec.run(payments)

    for kind in MatchKind:
        group = report.by_kind(kind)
        print(f"\n== {kind.value}: {len(group)}")
        for m in group:
            linked = " + ".join(f"{i.id} ({rub(i.amount)})" for i in m.invoices) or "—"
            print(f"  {m.payment.id}  {m.payment.customer_id:<14} {rub(m.payment.amount):>16}  →  {linked}")

    print(f"\nАвтоматически сверено: {report.auto_rate:.0%}")


if __name__ == "__main__":
    main()
