"""Аудит числовых настроек из переменных окружения: что на самом деле прочитает сервис.

Один и тот же `WORKERS=8 ` читают сервис на C (`atoi`/`strtol`) и сервис на Python (`int()`), и видят разное:
atoi молча отбрасывает хвост (`TIMEOUT=30s` → 30), превращает мусор в 0 (`WORKERS=auto` → 0), прижимает
переполнение (`MAX_BYTES=4294967296` → 2147483647); int() на тех же строках падает или понимает `1_000`.
Алгоритм: algos.parse_int_prefix (LeetCode 8).
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from algos import parse_int_prefix

C_WHITESPACE = " \t\n\v\f\r"   # isspace() в C: atoi пропускает всё это, LeetCode — только ' '

Issue = Literal["ok", "missing", "no_digits", "clamped", "trailing", "out_of_range"]
ISSUES: tuple[Issue, ...] = ("ok", "missing", "no_digits", "clamped", "trailing", "out_of_range")


@dataclass(frozen=True, slots=True)
class Setting:
    """Числовая настройка: имя переменной, тип в C-сервисе (bits/signed) и допустимый по смыслу диапазон."""
    name: str
    bits: int = 32
    signed: bool = True
    min: int | None = None
    max: int | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class Finding:
    name: str
    raw: str | None          # значение переменной как есть; None — не задана
    c_value: int | None      # что прочитает atoi/strtol в C-сервисе (None — переменной нет)
    py_value: int | None     # что прочитает int() в Python-сервисе (None — int() упадёт)
    issue: Issue
    message: str

    @property
    def diverges(self) -> bool:
        """C- и Python-сервис видят разные значения (или один из них падает)."""
        return self.raw is not None and self.c_value != self.py_value


def _py_int(raw: str) -> int | None:
    try:
        return int(raw)       # strip пробелов, '_' между цифрами, Unicode-цифры — всё это int() принимает
    except ValueError:
        return None


def check(setting: Setting, raw: str | None) -> Finding:
    """Проверяет одну переменную. Проблемы по убыванию серьёзности: первая найденная — в `issue`."""
    s = setting
    if raw is None:
        issue: Issue = "missing" if s.required else "ok"
        msg = "переменная не задана" if s.required else "не задана, будет значение по умолчанию"
        return Finding(s.name, None, None, None, issue, msg)

    py = _py_int(raw)
    r = parse_int_prefix(raw, bits=s.bits, signed=s.signed, whitespace=C_WHITESPACE)
    if r is None:
        return Finding(s.name, raw, 0, py, "no_digits",
                       f"нет числа в начале: atoi вернёт 0 без ошибки (int() → {'ошибка' if py is None else py})")
    if r.clamped:
        return Finding(s.name, raw, r.value, py, "clamped",
                       f"не помещается в {'' if s.signed else 'u'}int{s.bits}: atoi прижмёт к {r.value}")
    tail = raw[r.end:]
    if tail.strip(C_WHITESPACE):
        return Finding(s.name, raw, r.value, py, "trailing",
                       f"хвост {tail!r} отброшен молча: atoi видит {r.value}"
                       + ("" if py == r.value else f", а int() — {'ошибку' if py is None else py}"))
    if (s.min is not None and r.value < s.min) or (s.max is not None and r.value > s.max):
        return Finding(s.name, raw, r.value, py, "out_of_range",
                       f"{r.value} вне допустимого [{'−∞' if s.min is None else s.min}, "
                       f"{'∞' if s.max is None else s.max}]")
    return Finding(s.name, raw, r.value, py, "ok", "ok")


def audit_env(env: Mapping[str, str], settings: Sequence[Setting]) -> list[Finding]:
    """Проверяет все настройки по окружению `env` (например, os.environ). Порядок — как в `settings`."""
    return [check(s, env.get(s.name)) for s in settings]
