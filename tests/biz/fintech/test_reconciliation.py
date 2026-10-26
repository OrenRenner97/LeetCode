from datetime import date

import pytest

from algos import find_pair_with_sum
from biz.fintech.reconciliation import Invoice, MatchKind, Payment, Reconciler

D = date(2026, 10, 1)


def _inv(id_, amount, customer="A", due=D):
    return Invoice(id_, customer, amount, due)


def _ids(match):
    return sorted(i.id for i in match.invoices)


def test_single_has_priority_over_pair():
    rec = Reconciler()
    rec.add_invoices([_inv("1", 100), _inv("2", 200), _inv("3", 300)])
    m = rec.reconcile(Payment("p", "A", 300))
    assert m.kind is MatchKind.SINGLE and _ids(m) == ["3"]


def test_pair():
    rec = Reconciler()
    rec.add_invoices([_inv("1", 100), _inv("2", 250), _inv("3", 400)])
    m = rec.reconcile(Payment("p", "A", 650))
    assert m.kind is MatchKind.PAIR and _ids(m) == ["2", "3"]


def test_pair_of_equal_amounts():
    rec = Reconciler()
    rec.add_invoices([_inv("1", 500), _inv("2", 500)])
    m = rec.reconcile(Payment("p", "A", 1000))
    assert m.kind is MatchKind.PAIR and _ids(m) == ["1", "2"]


def test_closed_invoice_not_reused():
    rec = Reconciler()
    rec.add_invoices([_inv("1", 100)])
    assert rec.reconcile(Payment("p1", "A", 100)).kind is MatchKind.SINGLE
    assert rec.reconcile(Payment("p2", "A", 100)).kind is MatchKind.UNMATCHED


def test_other_customer_invoices_ignored():
    rec = Reconciler()
    rec.add_invoices([_inv("1", 100, "A"), _inv("2", 200, "B")])
    assert rec.reconcile(Payment("p", "A", 300)).kind is MatchKind.UNMATCHED


def test_older_invoices_closed_first():
    rec = Reconciler()
    rec.add_invoices([
        _inv("new", 100, due=date(2026, 12, 1)),
        _inv("old", 100, due=date(2026, 1, 1)),
    ])
    assert _ids(rec.reconcile(Payment("p", "A", 100))) == ["old"]


def test_older_pair_preferred():
    # 300 = 100 + 200 (старые) = 150 + 150 (новые) → закрываем старые.
    rec = Reconciler()
    rec.add_invoices([
        _inv("old1", 100, due=date(2026, 1, 1)),
        _inv("old2", 200, due=date(2026, 1, 2)),
        _inv("new1", 150, due=date(2026, 6, 1)),
        _inv("new2", 150, due=date(2026, 6, 2)),
    ])
    assert _ids(rec.reconcile(Payment("p", "A", 300))) == ["old1", "old2"]


@pytest.mark.parametrize("backend", find_pair_with_sum.backends)
def test_backend_is_passed_through(backend):
    rec = Reconciler(backend=backend)
    rec.add_invoices([_inv("1", 100), _inv("2", 250), _inv("3", 400)])
    assert _ids(rec.reconcile(Payment("p", "A", 350))) == ["1", "2"]
