import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
A, B, C = "0x" + "a1" * 20, "0x" + "b0" * 20, "0x" + "c4" * 20
E18 = 10**18


def test_simulate():
    r = client.post("/v1/crypto/ledger/simulate", json={
        "token": {"symbol": "ETH", "decimals": 18},
        "operations": [
            {"op": "mint", "to": A, "amount": "10"},
            {"op": "mint", "to": B, "amount": "0.000000000000000001"},
            {"op": "transfer", "from": B, "to": A, "amount": "1"},       # нехватка → откат
            {"op": "transfer", "from": A, "to": C, "amount": "2.5"},
            {"op": "burn", "from": C, "amount": "0.5"},
        ],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert {b["address"]: b["amount"] for b in body["balances"]} == {A: "7.5", C: "2", B: "0.000000000000000001"}
    assert body["total_supply"]["wei"] == str(95 * E18 // 10 + 1)
    assert [f["index"] for f in body["failed"]] == [2] and body["failed"][0]["error"] == "InsufficientBalance"
    assert body["events"][0]["from"] == "0x" + "0" * 40  # mint
    assert body["audit_ok"] is True


def test_simulate_overflow_is_reported_not_500():
    r = client.post("/v1/crypto/ledger/simulate", json={
        "token": {"symbol": "X", "decimals": 0},
        "operations": [{"op": "mint", "to": A, "amount": str(2**256 - 1)}, {"op": "mint", "to": B, "amount": "1"}],
    })
    assert r.status_code == 200
    assert r.json()["failed"][0]["error"] == "Uint256Overflow"


@pytest.mark.parametrize("op", [
    {"op": "transfer", "to": A, "amount": "1"},              # нет from
    {"op": "mint", "to": "0x123", "amount": "1"},            # плохой адрес
    {"op": "mint", "to": A, "amount": "1.5e3"},              # не строка-число
    {"op": "steal", "to": A, "amount": "1"},
])
def test_simulate_validation(op):
    r = client.post("/v1/crypto/ledger/simulate", json={"token": {"symbol": "ETH", "decimals": 18}, "operations": [op]})
    assert r.status_code == 422


def test_audit():
    ok = client.post("/v1/crypto/ledger/audit", json={"balances": [str(7 * E18), str(3 * E18)], "total_supply": str(10 * E18)})
    assert ok.json() == {"ok": True, "balances_sum": str(10 * E18), "total_supply": str(10 * E18),
                         "difference": "0", "holders": 2}
    bad = client.post("/v1/crypto/ledger/audit", json={"balances": [str(7 * E18), str(3 * E18 - 1)], "total_supply": str(10 * E18)})
    assert bad.json()["ok"] is False and bad.json()["difference"] == "-1"


def test_audit_rejects_over_uint256():
    r = client.post("/v1/crypto/ledger/audit", json={"balances": [str(2**256)], "total_supply": "0"})
    assert r.status_code == 422


def test_units():
    assert client.get("/v1/crypto/units/parse", params={"amount": "1.5"}).json()["wei"] == str(15 * E18 // 10)
    assert client.get("/v1/crypto/units/format", params={"wei": "1500000", "decimals": 6}).json()["amount"] == "1.5"
    assert client.get("/v1/crypto/units/parse", params={"amount": "0.1234567", "decimals": 6}).status_code == 422


def test_backends_endpoint():
    body = client.get("/backends").json()
    assert "python" in body["add_digits"] and "python" in body["sum_limbs"]
