"""Демо: python -m biz.fintech.scenarios.demo"""
import random
import re
import time
from datetime import datetime, timedelta

from .engine import ScenarioEngine, StreamingScenarioEngine, decide
from .models import Action, Mode, SessionEvent
from .rules import RuleError, ScenarioRule, lint_rules

CATALOG = {"login", "login_new_device", "login_failed", "login_success", "view_balance", "view_history",
           "change_phone", "change_email", "add_payee", "transfer", "payout", "logout"}

RULES = [
    ScenarioRule("ato_classic", "login_new_device .* change_phone .* payout", Action.BLOCK,
                 description="захват аккаунта: новое устройство → смена телефона → вывод"),
    ScenarioRule("new_payee_payout", "add_payee payout", Action.STEP_UP,
                 description="вывод сразу после добавления получателя, без единого действия между"),
    ScenarioRule("brute_force_success", "login_failed login_failed login_failed login_failed* login_success",
                 Action.STEP_UP, description="3+ неудачных входа подряд, затем удачный: подобран пароль"),
    ScenarioRule("bot_session", "login payout logout*", Action.REVIEW, Mode.SESSION,
                 description="вся сессия — вход и вывод, ничего не просмотрено: похоже на скрипт"),
]


def generate(seed: int = 10, normal: int = 3000) -> list[SessionEvent]:
    rng = random.Random(seed)
    t0 = datetime(2026, 11, 18, 9, 0)
    out: list[SessionEvent] = []

    def session(sid, user, kinds, start_min):
        for k, kind in enumerate(kinds):
            amount = rng.randrange(1_000, 50_000) * 100 if kind in ("payout", "transfer") else 0
            out.append(SessionEvent(f"E{len(out):06d}", sid, user, t0 + timedelta(minutes=start_min, seconds=20 * k),
                                    kind, amount))

    browse = ["view_balance", "view_history", "transfer", "view_balance"]
    for n in range(normal):
        kinds = [rng.choice(["login"] * 9 + ["login_new_device"])]
        kinds += rng.choices(browse, k=rng.randint(1, 6))
        if rng.random() < 0.05:
            kinds += ["add_payee", "view_balance", "payout"]          # честно: между ними есть действия
        if rng.random() < 0.02:
            kinds += ["change_email"]
        if rng.random() < 0.3:
            kinds += ["payout"]
        kinds += ["logout"] * (rng.random() < 0.6)
        session(f"S{n:05d}", f"user-{rng.randrange(800):03d}", kinds, rng.randrange(600))

    session("S-ato", "user-017", ["login_new_device", "view_balance", "change_phone", "view_history", "payout"], 120)
    session("S-ato-slow", "user-233", ["login_new_device", "change_phone", "logout"], 200)   # без вывода — нет тревоги
    session("S-payee", "user-402", ["login", "view_balance", "add_payee", "payout", "logout"], 300)
    session("S-brute", "user-555", ["login_failed"] * 5 + ["login_success", "view_balance", "logout"], 50)
    session("S-bot", "user-700", ["login", "payout", "logout"], 400)
    session("S-bot-not", "user-701", ["login", "payout", "view_balance", "logout"], 401)    # что-то смотрел
    rng.shuffle(out)                                                   # события приходят вперемешку
    return out


def show_alerts(alerts):
    for a in alerts:
        print(f"  [{a.action.value:<7}] {a.rule:<20} {a.session_id:<10} {a.user_id}  на «{a.trigger.kind}» "
              f"(событие {a.events_seen}, деньги в сессии {a.amount_seen / 100:,.2f} ₽)")


def main() -> None:
    print("== Правила")
    for r in RULES:
        print(f"  {r.name:<20} [{r.mode.value:<8} → {r.action.value:<7}] {r.pattern!r}: {r.description}")

    events = generate()
    sessions = {e.session_id for e in events}
    t = time.perf_counter()
    alerts = ScenarioEngine(RULES).scan(events)
    dt = time.perf_counter() - t
    print(f"\n== Пакетный режим: {len(events)} событий, {len(sessions)} сессий, {dt * 1000:.0f} ms → тревог {len(alerts)}")
    show_alerts(alerts)

    print("\n== Онлайн-режим: тревога на том событии, где сложился сценарий (вывод ещё можно остановить)")
    stream = StreamingScenarioEngine(RULES)
    for e in sorted((e for e in events if e.session_id == "S-ato"), key=lambda e: e.ts):
        fired = stream.observe(e)
        verdict = decide(fired)
        print(f"  {e.ts:%H:%M:%S} {e.kind:<17} → {verdict.value if verdict else 'пропустить'}")

    print("\n== Проверка правил аналитика при загрузке")
    for name, pattern in [("typo", "login_new_device .* chnage_phone .* payout"), ("always", "login* .*"),
                          ("bad", "login ** payout")]:
        try:
            rule = ScenarioRule(name, pattern)
            print(f"  {pattern!r}: загружено, предупреждения: {lint_rules([rule], CATALOG)}")
        except RuleError as exc:
            print(f"  {pattern!r}: отклонено — {exc}")

    print("\n== Почему не re: неаккуратное правило «login* » × k + «payout» на сессии из 2k входов без вывода")
    for k in (6, 8, 10):
        kinds = ["login"] * (2 * k) + ["logout"]
        rule = ScenarioRule("clumsy", "login* " * k + "payout", mode=Mode.SESSION)
        t = time.perf_counter()
        st = rule.compiled.start()
        for kind in kinds:
            st = rule.compiled.step(st, kind)
        ours = time.perf_counter() - t
        text, rx = "L" * (2 * k) + "O", "L*" * k + "P"           # то же правило на re: по букве на событие
        t = time.perf_counter()
        re.fullmatch(rx, text)
        theirs = time.perf_counter() - t
        print(f"  k = {k:>2}: НКА {ours * 1e6:7.0f} µs   re {theirs * 1e3:9.1f} ms")


if __name__ == "__main__":
    main()
