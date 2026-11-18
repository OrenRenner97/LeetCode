"""Правила-сценарии: шаблон над типами событий, который пишет аналитик антифрода.

Синтаксис (токены через пробел):
    login_new_device      — ровно это событие
    .                     — любое одно событие
    имя*  /  .*           — ноль или больше таких событий
Пример: "login_new_device .* change_phone .* payout" — вход с нового устройства, потом (через что угодно)
смена телефона, потом вывод денег. Классический захват аккаунта (account takeover, ATO).

Почему не обычные регулярные выражения (`re`): правила пишут люди, а `re` на шаблоне вида «a*a*a*…»
работает экспоненциально (ReDoS, README задачи 10). Одно неудачное правило повесило бы обработку платежей.
Здесь шаблон компилируется в НКА (`algos.automata`), и время линейно на любом правиле и любой сессии.
"""
import re
from dataclasses import dataclass, field

from algos.automata import ANY, SimplePattern

from .models import Action, Mode

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class RuleError(ValueError):
    """Правило написано с ошибкой. Ловится при загрузке правил, а не молча на проде."""


@dataclass(frozen=True)
class ScenarioRule:
    name: str
    pattern: str
    action: Action = Action.REVIEW
    mode: Mode = Mode.CONTAINS
    description: str = ""
    compiled: SimplePattern = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "compiled", compile_rule(self.pattern, self.mode, rule=self.name))


def parse_tokens(pattern: str, *, rule: str = "?") -> list[tuple[object, bool]]:
    """Текст правила → токены (событие или ANY, звезда?)."""
    if not isinstance(pattern, str):
        raise RuleError(f"{rule}: шаблон должен быть строкой")
    tokens = []
    for word in pattern.split():
        star = word.endswith("*")
        name = word[:-1] if star else word
        if name == ".":
            tokens.append((ANY, star))
        elif _NAME.match(name):
            tokens.append((name, star))
        else:
            raise RuleError(f"{rule}: «{word}» — ожидается имя события (a-z, 0-9, _), «.» или с «*» на конце")
    if not tokens:
        raise RuleError(f"{rule}: пустой шаблон")
    return tokens


def compile_rule(pattern: str, mode: Mode, *, rule: str = "?") -> SimplePattern:
    tokens = parse_tokens(pattern, rule=rule)
    if mode is Mode.CONTAINS:
        tokens = [(ANY, True), *tokens, (ANY, True)]   # «где-то в сессии» = .* шаблон .*
    compiled = SimplePattern.from_tokens(tokens)
    if mode is Mode.CONTAINS and compiled.fullmatch(()):
        # «.*», «login*» и т.п.: сценарий из одних необязательных шагов срабатывает на КАЖДОЙ сессии.
        raise RuleError(f"{rule}: шаблон совпадает с пустой последовательностью — сработает на любой сессии")
    return compiled


def lint_rules(rules: list[ScenarioRule], known_events: set[str] | None) -> list[str]:
    """Предупреждения, которые не делают правило неверным, но почти наверняка ошибка:
    - событие, которого нет в каталоге (опечатка «chnage_phone» — правило молча никогда не сработает);
    - два правила с одним именем (в отчёте не различить).
    """
    warnings = []
    seen = set()
    for r in rules:
        if r.name in seen:
            warnings.append(f"{r.name}: имя правила повторяется")
        seen.add(r.name)
        if known_events is not None:
            for elem, _ in parse_tokens(r.pattern, rule=r.name):
                if elem is not ANY and elem not in known_events:
                    warnings.append(f"{r.name}: события «{elem}» нет в каталоге — правило не сработает никогда")
    return warnings
