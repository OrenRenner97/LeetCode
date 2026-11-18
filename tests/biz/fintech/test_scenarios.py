import random
import time
from datetime import datetime, timedelta

import pytest

from biz.fintech.scenarios import (Action, Mode, RuleError, ScenarioEngine, ScenarioRule, SessionEvent,
                                   StreamingScenarioEngine, decide, lint_rules)
from biz.fintech.scenarios.demo import CATALOG, RULES, generate

T0 = datetime(2026, 11, 18, 9, 0)
ATO = ScenarioRule("ato", "login_new_device .* change_phone .* payout", Action.BLOCK)


def _session(sid, kinds, user="u", start=0, amount=0):
    return [SessionEvent(f"{sid}-{k}", sid, user, T0 + timedelta(seconds=start + k), kind,
                         amount if kind == "payout" else 0)
            for k, kind in enumerate(kinds.split())]


def test_ato_fires_on_payout_in_stream():
    stream = StreamingScenarioEngine([ATO])
    verdicts = [decide(stream.observe(e)) for e in _session("s", "login_new_device view change_phone view payout logout")]
    assert verdicts == [None, None, None, None, Action.BLOCK, None]   # ровно на выводе, один раз


@pytest.mark.parametrize("kinds", [
    "login_new_device change_phone logout",          # нет вывода
    "login change_phone payout",                     # не новое устройство
    "login_new_device payout change_phone",          # порядок другой
    "change_phone login_new_device payout",
])
def test_ato_no_alert(kinds):
    assert ScenarioEngine([ATO]).scan(_session("s", kinds)) == []


def test_contains_vs_session_mode():
    contains = ScenarioRule("c", "login payout")
    session = ScenarioRule("s", "login payout logout*", mode=Mode.SESSION)
    engine = ScenarioEngine([contains, session])
    assert {a.rule for a in engine.scan(_session("a", "login payout logout"))} == {"c", "s"}
    assert {a.rule for a in engine.scan(_session("b", "login payout view logout"))} == {"c"}   # сессия шире шаблона
    assert {a.rule for a in engine.scan(_session("c", "view login payout"))} == {"c"}


def test_batch_sorts_and_separates_sessions():
    events = _session("a", "login_new_device change_phone payout", user="alice") + \
        _session("b", "login_new_device view logout", user="bob")
    random.Random(1).shuffle(events)
    [al] = ScenarioEngine([ATO]).scan(events)
    assert al.session_id == "a" and al.user_id == "alice" and al.trigger.kind == "payout" and al.events_seen == 3
    # события одной сессии с двух устройств не смешиваются с чужими: change_phone в «b» не помогает «c»
    events = _session("b", "change_phone") + _session("c", "login_new_device payout")
    assert ScenarioEngine([ATO]).scan(events) == []


def test_alert_amount_and_severity_order():
    rules = [ScenarioRule("r", "payout"), ATO, ScenarioRule("s", "add_payee payout", Action.STEP_UP)]
    alerts = ScenarioEngine(rules).scan(_session("x", "login_new_device change_phone add_payee payout", amount=150_000))
    assert [a.action for a in alerts] == [Action.BLOCK, Action.STEP_UP, Action.REVIEW]
    assert all(a.amount_seen == 150_000 for a in alerts) and decide(alerts) is Action.BLOCK
    assert decide([]) is None


def test_stream_requires_time_order_and_closes_idle():
    stream = StreamingScenarioEngine([ScenarioRule("bot", "login payout", mode=Mode.SESSION)])
    e1, e2 = _session("s", "login payout")
    stream.observe(e2)
    with pytest.raises(ValueError):
        stream.observe(e1)
    stream = StreamingScenarioEngine([ScenarioRule("bot", "login payout", mode=Mode.SESSION)])
    stream.observe(e1)
    stream.observe(e2)
    assert stream.close_idle(T0 + timedelta(minutes=5)) == [] and stream.open_sessions == 1
    [al] = stream.close_idle(T0 + timedelta(hours=1))
    assert al.rule == "bot" and stream.open_sessions == 0
    assert stream.close_session("unknown") == []


def test_rule_validation_and_lint():
    for bad in ("", "   ", "login ** payout", "Login", "pay-out", "*", ".* login*"):
        with pytest.raises(RuleError):
            ScenarioRule("bad", bad)
    ScenarioRule("ok", ".* login*", mode=Mode.SESSION)           # для всей сессии пустой шаблон допустим
    rules = [ScenarioRule("t", "login chnage_phone"), ScenarioRule("t", "login")]
    warnings = lint_rules(rules, CATALOG)
    assert any("chnage_phone" in w for w in warnings) and any("повторяется" in w for w in warnings)
    assert lint_rules(RULES, CATALOG) == []


def test_no_redos_on_clumsy_rule():
    rule = ScenarioRule("clumsy", "login* " * 40 + "payout", mode=Mode.SESSION)
    events = _session("s", " ".join(["login"] * 80 + ["logout"]))
    t = time.perf_counter()
    assert ScenarioEngine([rule]).scan(events) == []
    assert time.perf_counter() - t < 0.1                          # re.fullmatch считал бы здесь вечность


def test_demo_finds_exactly_the_planted_fraud():
    alerts = ScenarioEngine(RULES).scan(generate(normal=1000))
    assert {(a.session_id, a.rule) for a in alerts} == {
        ("S-ato", "ato_classic"), ("S-payee", "new_payee_payout"),
        ("S-brute", "brute_force_success"), ("S-bot", "bot_session")}
