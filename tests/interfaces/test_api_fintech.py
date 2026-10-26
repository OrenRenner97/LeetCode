import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)

PAYLOAD = {
    "invoices": [
        {"id": "INV-1", "customer_id": "A", "amount": 10000, "due": "2026-09-01"},
        {"id": "INV-2", "customer_id": "A", "amount": 25000, "due": "2026-09-05"},
        {"id": "INV-3", "customer_id": "A", "amount": 40000, "due": "2026-09-10"},
        {"id": "INV-4", "customer_id": "B", "amount": 7000, "due": "2026-09-01"},
    ],
    "payments": [
        {"id": "P-1", "customer_id": "A", "amount": 65000},
        {"id": "P-2", "customer_id": "B", "amount": 7000},
        {"id": "P-3", "customer_id": "A", "amount": 1},
    ],
}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_backends_lists_python():
    assert "python" in client.get("/backends").json()["find_pair_with_sum"]


def test_reconcile():
    r = client.post("/v1/fintech/reconcile", json=PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["matches"] == [
        {"payment_id": "P-1", "kind": "pair", "invoice_ids": ["INV-2", "INV-3"]},
        {"payment_id": "P-2", "kind": "single", "invoice_ids": ["INV-4"]},
        {"payment_id": "P-3", "kind": "unmatched", "invoice_ids": []},
    ]
    assert body["summary"] == {"single": 1, "pair": 1, "unmatched": 1}


def test_unknown_backend_is_400():
    r = client.post("/v1/fintech/reconcile", json={**PAYLOAD, "backend": "quantum"})
    assert r.status_code == 400
    assert "quantum" in r.json()["detail"]


def test_validation_rejects_negative_amount():
    bad = {**PAYLOAD, "payments": [{"id": "P", "customer_id": "A", "amount": -5}]}
    assert client.post("/v1/fintech/reconcile", json=bad).status_code == 422
