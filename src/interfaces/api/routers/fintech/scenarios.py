from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, model_validator

from biz.fintech.scenarios import Action, Mode, RuleError, ScenarioEngine, ScenarioRule, SessionEvent, decide, lint_rules

router = APIRouter(prefix="/scenarios", tags=["fintech/scenarios"])

ActionStr = Literal["review", "step_up", "block"]
ModeStr = Literal["contains", "session"]
_PATTERN_HELP = ("Шаблон над типами событий через пробел: `имя` — это событие, `.` — любое одно, "
                 "`имя*` / `.*` — ноль или больше. Пример: `login_new_device .* change_phone .* payout`")


class RuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Имя правила: видно в тревогах", examples=["ato_classic"])
    pattern: str = Field(min_length=1, max_length=2000, description=_PATTERN_HELP,
                         examples=["login_new_device .* change_phone .* payout"])
    action: ActionStr = Field("review", description="Что делать при срабатывании: `review` — аналитику, "
                                                    "`step_up` — запросить 2FA, `block` — остановить операцию")
    mode: ModeStr = Field("contains", description="`contains` — сценарий где-то в сессии, тревога сразу на его последнем "
                                                  "событии; `session` — шаблон описывает всю сессию целиком")

    def to_rule(self) -> ScenarioRule:
        return ScenarioRule(self.name, self.pattern, Action(self.action), Mode(self.mode))


class RuleInChecked(RuleIn):
    @model_validator(mode="after")
    def _compiles(self):
        self.to_rule()          # RuleError — это ValueError: pydantic вернёт 422 с текстом ошибки
        return self


class EventIn(BaseModel):
    id: str = Field(description="Идентификатор события", examples=["E-000123"])
    session_id: str = Field(description="Сессия: сценарии ищутся внутри одной сессии", examples=["S-42"])
    user_id: str = Field(description="Пользователь (для отчёта)", examples=["user-017"])
    ts: datetime = Field(description="Время события: внутри сессии события упорядочиваются по нему")
    kind: str = Field(min_length=1, max_length=100, description="Тип события из каталога", examples=["payout"])
    amount: int = Field(0, ge=0, description="Сумма в копейках для денежных событий, иначе 0", examples=[2_500_000])


class ScanRequest(BaseModel):
    rules: list[RuleInChecked] = Field(min_length=1, max_length=500, description="Правила-сценарии")
    events: list[EventIn] = Field(max_length=200_000, description="События за период в любом порядке, из любых сессий")


class AlertOut(BaseModel):
    rule: str = Field(description="Сработавшее правило")
    action: ActionStr = Field(description="Действие правила")
    session_id: str = Field(description="Сессия")
    user_id: str = Field(description="Пользователь")
    trigger_event_id: str = Field(description="Событие, на котором сложился сценарий (для `session` — последнее событие сессии)")
    trigger_kind: str = Field(description="Тип этого события")
    trigger_ts: datetime = Field(description="Время срабатывания")
    session_started: datetime = Field(description="Первое событие сессии")
    events_seen: int = Field(description="Событий сессии до срабатывания включительно")
    amount_seen: int = Field(description="Сумма денежных событий сессии до срабатывания, копейки")


class SessionDecision(BaseModel):
    session_id: str = Field(description="Сессия")
    action: ActionStr = Field(description="Самое строгое действие из сработавших правил")
    rules: list[str] = Field(description="Какие правила сработали")


class ScanResponse(BaseModel):
    alerts: list[AlertOut] = Field(description="Тревоги: сначала `block`, потом `step_up`, потом `review`; внутри — по времени")
    decisions: list[SessionDecision] = Field(description="Итог по каждой сессии с тревогами")
    scanned_events: int = Field(description="Сколько событий проверено")
    scanned_sessions: int = Field(description="Сколько разных сессий")


class CheckRequest(BaseModel):
    rules: list[RuleIn] = Field(min_length=1, max_length=500, description="Правила для проверки")
    known_events: list[str] | None = Field(None, description="Каталог типов событий: имя вне каталога — предупреждение "
                                                             "(опечатка делает правило мёртвым)",
                                           examples=[["login", "login_new_device", "change_phone", "payout"]])


class RuleCheck(BaseModel):
    name: str = Field(description="Имя правила")
    ok: bool = Field(description="Правило корректно и будет загружено")
    error: str | None = Field(description="Почему отклонено (если `ok = false`)")


class CheckResponse(BaseModel):
    rules: list[RuleCheck] = Field(description="Результат по каждому правилу, в порядке запроса")
    warnings: list[str] = Field(description="Подозрительное, но допустимое: события вне каталога, повтор имён")


def _ev(k, sid, kind, minute, amount=0):
    return {"id": f"E-{sid}-{k}", "session_id": sid, "user_id": f"user-{sid}", "ts": f"2026-11-18T10:{minute:02d}:00Z",
            "kind": kind, "amount": amount}


_ATO_RULE = {"name": "ato_classic", "pattern": "login_new_device .* change_phone .* payout", "action": "block"}
_SCAN_EXAMPLES = {
    "ato": {
        "summary": "Захват аккаунта",
        "description": "Новое устройство → смена телефона → вывод: `block` на событии вывода. "
                       "Вторая сессия без смены телефона — без тревоги.",
        "value": {"rules": [_ATO_RULE],
                  "events": [_ev(k, "S1", kind, k, 2_500_000 if kind == "payout" else 0) for k, kind in
                             enumerate(["login_new_device", "view_balance", "change_phone", "payout"])]
                  + [_ev(k, "S2", kind, k) for k, kind in enumerate(["login_new_device", "view_balance", "payout"])]},
    },
    "bot_session": {
        "summary": "Сессия-скрипт целиком",
        "description": "Правило `session`: вся сессия — вход, вывод и, может быть, выход. Ничего не просмотрено.",
        "value": {"rules": [{"name": "bot_session", "pattern": "login payout logout*", "mode": "session"}],
                  "events": [_ev(k, "S3", kind, k, 100_000 if kind == "payout" else 0) for k, kind in
                             enumerate(["login", "payout", "logout"])]},
    },
}
_CHECK_EXAMPLES = {
    "mixed": {
        "summary": "Опечатка, правило-«всегда» и корректное",
        "description": "Опечатка в имени события — предупреждение; шаблон, совпадающий с пустой сессией, — отклонён.",
        "value": {"rules": [_ATO_RULE,
                            {"name": "typo", "pattern": "login_new_device .* chnage_phone .* payout"},
                            {"name": "always", "pattern": "login* .*"}],
                  "known_events": ["login", "login_new_device", "change_phone", "payout"]},
    },
}


@router.post("/scan", summary="Найти мошеннические сценарии в сессиях")
def scan_scenarios(req: Annotated[ScanRequest, Body(openapi_examples=_SCAN_EXAMPLES)]) -> ScanResponse:
    """Ищет в событиях сессий сценарии из правил аналитика: например, захват аккаунта
    «вход с нового устройства → смена телефона → вывод».

    Правило — шаблон с `.` и `*` над типами событий (**LeetCode 10. Regular Expression Matching**).
    Шаблоны компилируются в НКА (`algos.automata`): время линейно на любом правиле, в отличие от `re`,
    который на неаккуратном правиле уходит в экспоненту (ReDoS). Некорректное правило — 422.
    Бизнес-логика: `biz.fintech.scenarios`.
    """
    rules = [r.to_rule() for r in req.rules]
    events = [SessionEvent(**e.model_dump()) for e in req.events]
    alerts = ScenarioEngine(rules).scan(events)
    by_session: dict[str, list] = {}
    for a in alerts:
        by_session.setdefault(a.session_id, []).append(a)
    return ScanResponse(
        alerts=[AlertOut(rule=a.rule, action=a.action.value, session_id=a.session_id, user_id=a.user_id,
                         trigger_event_id=a.trigger.id, trigger_kind=a.trigger.kind, trigger_ts=a.trigger.ts,
                         session_started=a.started, events_seen=a.events_seen, amount_seen=a.amount_seen)
                for a in alerts],
        decisions=[SessionDecision(session_id=sid, action=decide(als).value, rules=[a.rule for a in als])
                   for sid, als in by_session.items()],
        scanned_events=len(events),
        scanned_sessions=len({e.session_id for e in events}),
    )


@router.post("/rules/check", summary="Проверить правила перед загрузкой")
def check_scenario_rules(req: Annotated[CheckRequest, Body(openapi_examples=_CHECK_EXAMPLES)]) -> CheckResponse:
    """Проверяет правила аналитика, не запуская их: синтаксис, правило-«всегда» (совпадает с пустой сессией),
    события вне каталога, повтор имён. Ошибки возвращаются по каждому правилу в теле ответа, а не 422:
    аналитик видит все проблемы сразу, а не первую.
    """
    checks, valid = [], []
    for r in req.rules:
        try:
            valid.append(r.to_rule())
            checks.append(RuleCheck(name=r.name, ok=True, error=None))
        except RuleError as exc:
            checks.append(RuleCheck(name=r.name, ok=False, error=str(exc)))
    known = set(req.known_events) if req.known_events is not None else None
    return CheckResponse(rules=checks, warnings=lint_rules(valid, known))
