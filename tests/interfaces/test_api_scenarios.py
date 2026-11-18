import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from interfaces.api.main import app  # noqa: E402

client = TestClient(app)
ATO = {"name": "ato", "pattern": "login_new_device .* change_phone .* payout", "action": "block"}


def _ev(k, sid, kind, amount=0):
    return {"id": f"{sid}-{k}", "session_id": sid, "user_id": f"u-{sid}", "ts": f"2026-11-18T10:00:{k:02d}Z",
            "kind": kind, "amount": amount}


def _session(sid, kinds, amount=0):
    return [_ev(k, sid, kind, amount if kind == "payout" else 0) for k, kind in enumerate(kinds.split())]


def test_scan_finds_ato_and_decides():
    events = _session("S1", "login_new_device view change_phone add_payee payout", 2_500_000) + \
        _session("S2", "login_new_device view payout")
    rules = [ATO, {"name": "payee", "pattern": "add_payee payout", "action": "step_up"}]
    r = client.post("/v1/fintech/scenarios/scan", json={"rules": rules, "events": events[::-1]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scanned_events"] == 8 and body["scanned_sessions"] == 2
    assert [(a["rule"], a["action"], a["trigger_event_id"]) for a in body["alerts"]] == \
        [("ato", "block", "S1-4"), ("payee", "step_up", "S1-4")]
    assert body["alerts"][0]["amount_seen"] == 2_500_000 and body["alerts"][0]["events_seen"] == 5
    assert body["decisions"] == [{"session_id": "S1", "action": "block", "rules": ["ato", "payee"]}]


def test_session_mode():
    rule = {"name": "bot", "pattern": "login payout logout*", "mode": "session"}
    r = client.post("/v1/fintech/scenarios/scan",
                    json={"rules": [rule], "events": _session("A", "login payout logout") + _session("B", "login view payout")})
    assert [a["session_id"] for a in r.json()["alerts"]] == ["A"]


@pytest.mark.parametrize("pattern", ["login ** payout", ".*", "Pay-Out"])
def test_bad_rule_is_422(pattern):
    r = client.post("/v1/fintech/scenarios/scan", json={"rules": [{"name": "x", "pattern": pattern}], "events": []})
    assert r.status_code == 422


def test_rules_check_reports_everything():
    rules = [ATO, {"name": "typo", "pattern": "login chnage_phone"}, {"name": "always", "pattern": "login* .*"},
             {"name": "ato", "pattern": "payout"}]
    r = client.post("/v1/fintech/scenarios/rules/check",
                    json={"rules": rules, "known_events": ["login", "login_new_device", "change_phone", "payout"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [c["ok"] for c in body["rules"]] == [True, True, False, True]
    assert "пуст" in body["rules"][2]["error"]
    assert any("chnage_phone" in w for w in body["warnings"]) and any("повторяется" in w for w in body["warnings"])
