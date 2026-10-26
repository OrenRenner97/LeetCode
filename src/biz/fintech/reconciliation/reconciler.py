from collections import defaultdict
from collections.abc import Iterable

from algos import find_pair_with_sum

from .models import Invoice, Match, MatchKind, Payment, Report


class Reconciler:
    """Сопоставляет платежи с открытыми счетами клиента.

    Правила, по приоритету:
      1. Платёж равен одному счёту → закрываем его.
      2. Платёж равен сумме двух счетов → Two Sum, закрываем оба.
      3. Иначе платёж уходит на ручной разбор (частичная оплата, переплата, ошибка в сумме).

    Счета перебираются по сроку оплаты, так что при нескольких подходящих
    вариантах закрываются самые старые долги.

    backend передаётся в algos как есть (None → ALGOS_BACKEND или "auto").
    """

    def __init__(self, backend: str | None = None):
        # customer_id -> {invoice_id: Invoice}; закрытые счета удаляются,
        # поэтому один счёт нельзя оплатить дважды.
        self._open: dict[str, dict[str, Invoice]] = defaultdict(dict)
        self._backend = backend

    def add_invoices(self, invoices: Iterable[Invoice]) -> None:
        for inv in invoices:
            self._open[inv.customer_id][inv.id] = inv

    def open_invoices(self, customer_id: str) -> list[Invoice]:
        return sorted(self._open[customer_id].values(), key=lambda i: (i.due, i.id))

    def reconcile(self, payment: Payment) -> Match:
        invoices = self.open_invoices(payment.customer_id)

        for inv in invoices:
            if inv.amount == payment.amount:
                return self._close(payment, MatchKind.SINGLE, inv)

        pair = find_pair_with_sum(
            [inv.amount for inv in invoices], payment.amount, backend=self._backend
        )
        if pair:
            i, j = pair
            return self._close(payment, MatchKind.PAIR, invoices[i], invoices[j])

        return Match(payment, MatchKind.UNMATCHED)

    def run(self, payments: Iterable[Payment]) -> Report:
        report = Report()
        for p in payments:
            report.matches.append(self.reconcile(p))
        return report

    def _close(self, payment: Payment, kind: MatchKind, *invoices: Invoice) -> Match:
        for inv in invoices:
            del self._open[inv.customer_id][inv.id]
        return Match(payment, kind, invoices)
