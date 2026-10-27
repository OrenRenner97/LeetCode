import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
T = "2026-10-27T12:00:{:02d}+03:00"


def _trade(venue, price, sec):
    return {"venue": venue, "price": price, "ts": T.format(sec)}


def test_fair_price_with_checks():
    # Сделки нарочно не по времени: ручка сортирует сама.
    body = {
        "now": T.format(59),
        "trades": [_trade("A", 104, 30), _trade("A", 100, 10), _trade("A", 102, 20),
                   _trade("B", 103, 50), _trade("B", 101, 40)],
        "check_prices": [102, 110],
    }
    r = client.post("/v1/fintech/fair-price", json=body)
    assert r.status_code == 200
    data = r.json()
    assert (data["status"], data["price"], data["p25"], data["p75"], data["trades"]) == ("ok", 102, 101, 103, 5)
    assert [c["verdict"] for c in data["checks"]] == ["ok", "off_market"]
    assert [v["state"] for v in data["venues"]] == ["ok", "ok"]


def test_outlier_and_disputed():
    outlier = {"now": T.format(59), "trades": [_trade("A", 10_000, 50), _trade("B", 10_001, 50), _trade("X", 1_000_000, 50)]}
    data = client.post("/v1/fintech/fair-price", json=outlier).json()
    assert data["price"] == 10_000 and {v["venue"]: v["state"] for v in data["venues"]}["X"] == "outlier"

    disputed = {"now": T.format(59), "trades": [_trade("A", 10_000, 50), _trade("B", 10_300, 50)],
                "check_prices": [10_000]}
    data = client.post("/v1/fintech/fair-price", json=disputed).json()
    assert data["status"] == "disputed" and data["price"] is None
    assert data["checks"][0]["verdict"] == "no_fair_price"


def test_stale_by_rule():
    body = {"now": T.format(59), "trades": [_trade("A", 100, 55), _trade("B", 100, 0)],
            "rule": {"stale_after_s": 30}}
    data = client.post("/v1/fintech/fair-price", json=body).json()
    assert data["status"] == "insufficient"
    assert {v["venue"]: v["state"] for v in data["venues"]} == {"A": "ok", "B": "stale"}


def test_validation():
    naive = {"now": "2026-10-27T12:00:59", "trades": []}  # без часового пояса — нельзя сравнивать времена
    assert client.post("/v1/fintech/fair-price", json=naive).status_code == 422
    bad_price = {"now": T.format(59), "trades": [_trade("A", 0, 1)]}
    assert client.post("/v1/fintech/fair-price", json=bad_price).status_code == 422
