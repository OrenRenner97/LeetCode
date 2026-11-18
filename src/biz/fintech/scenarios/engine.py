"""Движок сценариев: онлайн (событие за событием) и пакетный (история за период).

Пакетный режим — это онлайн, прогнанный по отсортированной истории: результаты двух режимов совпадают
по построению, и логика срабатывания живёт в одном месте.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Action, Alert, Mode, SessionEvent
from .rules import ScenarioRule


@dataclass
class _Session:
    user_id: str
    started: datetime
    last_ts: datetime
    states: list[int]                     # состояние НКА по каждому правилу; 0 — правило уже не сработает (или уже сработало)
    events: int = 0
    amount: int = 0


class StreamingScenarioEngine:
    """Онлайн-режим: observe(event) на каждое событие, тревога — на том событии, где сложился сценарий.

    Для правил CONTAINS это главное: тревога приходит на событии `payout`, ДО того как деньги ушли,
    и операцию ещё можно остановить. Память — O(число правил) на открытую сессию, сами события не хранятся.
    Правило срабатывает в сессии не больше одного раза.
    """

    def __init__(self, rules: Iterable[ScenarioRule]):
        self.rules = list(rules)
        self._sessions: dict[str, _Session] = {}

    @property
    def open_sessions(self) -> int:
        return len(self._sessions)

    def observe(self, event: SessionEvent) -> list[Alert]:
        """Учесть событие. Возвращает тревоги CONTAINS-правил, сработавших на нём (строгие первыми)."""
        sess = self._sessions.get(event.session_id)
        if sess is None:
            sess = _Session(event.user_id, event.ts, event.ts, [r.compiled.start() for r in self.rules])
            self._sessions[event.session_id] = sess
        elif event.ts < sess.last_ts:
            raise ValueError(f"сессия {event.session_id}: событие {event.id} старше предыдущего — "
                             f"онлайн-режим требует порядка по времени (пакетный режим сортирует сам)")
        sess.last_ts = event.ts
        sess.events += 1
        sess.amount += event.amount
        alerts = []
        for i, rule in enumerate(self.rules):
            state = sess.states[i]
            if not state:
                continue
            state = rule.compiled.step(state, event.kind)
            sess.states[i] = state
            if rule.mode is Mode.CONTAINS and rule.compiled.accepts(state):
                sess.states[i] = 0                # дальше это правило в сессии не считаем
                alerts.append(self._alert(rule, event, sess))
        return _by_severity(alerts)

    def close_session(self, session_id: str, last_event: SessionEvent | None = None) -> list[Alert]:
        """Сессия закончилась (logout, таймаут): решаем SESSION-правила, описывающие сессию целиком."""
        sess = self._sessions.pop(session_id, None)
        if sess is None:
            return []
        alerts = []
        for i, rule in enumerate(self.rules):
            if rule.mode is Mode.SESSION and rule.compiled.accepts(sess.states[i]):
                trigger = last_event or SessionEvent("", session_id, sess.user_id, sess.last_ts, "session_closed")
                alerts.append(self._alert(rule, trigger, sess))
        return _by_severity(alerts)

    def close_idle(self, now: datetime, idle: timedelta = timedelta(minutes=30)) -> list[Alert]:
        """Закрыть сессии без событий дольше idle (как таймаут сессии на сайте). Освобождает память."""
        stale = [sid for sid, s in self._sessions.items() if now - s.last_ts > idle]
        return _by_severity([a for sid in stale for a in self.close_session(sid)])

    @staticmethod
    def _alert(rule: ScenarioRule, trigger: SessionEvent, sess: _Session) -> Alert:
        return Alert(rule.name, rule.action, trigger.session_id, sess.user_id, trigger, sess.started,
                     sess.events, sess.amount)


class ScenarioEngine:
    """Пакетный режим: события за период в любом порядке → все тревоги."""

    def __init__(self, rules: Iterable[ScenarioRule]):
        self.rules = list(rules)

    def scan(self, events: Iterable[SessionEvent]) -> list[Alert]:
        by_session: dict[str, list[SessionEvent]] = {}
        for e in events:
            by_session.setdefault(e.session_id, []).append(e)
        stream = StreamingScenarioEngine(self.rules)
        alerts = []
        for sid, evs in by_session.items():
            evs.sort(key=lambda e: e.ts)          # sort стабилен: одновременные события — в порядке прихода
            for e in evs:
                alerts += stream.observe(e)
            alerts += stream.close_session(sid, evs[-1])
        return _by_severity(alerts)


def decide(alerts: Iterable[Alert]) -> Action | None:
    """Итоговое действие по сессии: самое строгое из сработавших, None — пропустить."""
    return max((a.action for a in alerts), key=lambda a: a.severity, default=None)


def _by_severity(alerts: list[Alert]) -> list[Alert]:
    return sorted(alerts, key=lambda a: (-a.action.severity, a.trigger.ts, a.session_id))
