import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
URL = "/v1/fintech/antifraud/card-testing"


def _att(k, source, card, status="declined"):
    return {"id": f"{source}-{k}", "ts": f"2026-10-24T12:00:{k:02d}Z", "source": source,
            "card_fp": f"fingerprint-{card}", "card_last4": "4242", "amount": 100, "status": status}


def test_detects_card_testing():
    attempts = [_att(k, "bad", k) for k in range(6)] + [_att(k, "good", 0, "approved") for k in range(6)]
    r = client.post(URL, json={"attempts": attempts})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scanned_attempts"] == 12 and body["scanned_sources"] == 2
    [al] = body["alerts"]
    assert al["source"] == "bad" and al["risk"] == "high" and al["action"] == "block"
    assert al["distinct_cards"] == 6 and al["attempt_ids"] == [f"bad-{k}" for k in range(6)]


def test_rule_params():
    attempts = [_att(k, "x", k // 2) for k in range(12)]  # каждая карта дважды
    assert client.post(URL, json={"attempts": attempts}).json()["alerts"] == []
    r = client.post(URL, json={"attempts": attempts, "rule": {"max_repeats": 2}})
    assert r.json()["alerts"][0]["distinct_cards"] == 6


@pytest.mark.parametrize("bad", [
    {"card_fp": "4111111111111111"},     # PAN вместо отпечатка
    {"card_fp": "4111 1111 1111 1111"},
    {"card_last4": "42"},
    {"status": "maybe"},
])
def test_validation(bad):
    r = client.post(URL, json={"attempts": [{**_att(0, "s", 0), **bad}]})
    assert r.status_code == 422


def test_rule_validation():
    r = client.post(URL, json={"attempts": [], "rule": {"min_cards": 1}})
    assert r.status_code == 422
