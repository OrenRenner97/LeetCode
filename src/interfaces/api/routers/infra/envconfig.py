from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from biz.infra.envconfig import ISSUES, Setting, audit_env

router = APIRouter(prefix="/envconfig", tags=["infra/envconfig"])

IssueName = Literal["ok", "missing", "no_digits", "clamped", "trailing", "out_of_range"]
assert set(IssueName.__args__) == set(ISSUES)


class SettingIn(BaseModel):
    name: str = Field(min_length=1, max_length=256, description="Имя переменной окружения")
    bits: int = Field(32, ge=1, le=64, description="Ширина целого, в которое её читает C-сервис")
    signed: bool = Field(True, description="Знаковое ли это целое")
    min: int | None = Field(None, description="Минимум по смыслу настройки (например, WORKERS ≥ 1)")
    max: int | None = Field(None, description="Максимум по смыслу настройки")
    required: bool = Field(True, description="`false` — отсутствие не ошибка (есть значение по умолчанию)")


class AuditRequest(BaseModel):
    env: dict[str, str] = Field(max_length=10_000, description="Переменные окружения: имя → значение строкой")
    settings: list[SettingIn] | None = Field(
        None, max_length=10_000,
        description="Какие переменные числовые и в какой тип читаются. По умолчанию — все из `env` как int32")


class FindingOut(BaseModel):
    name: str = Field(description="Имя переменной")
    raw: str | None = Field(description="Значение как есть; `null` — переменная не задана")
    c_value: int | None = Field(description="Что прочитает `atoi`/`strtol` в C-сервисе")
    py_value: int | None = Field(description="Что прочитает `int()` в Python-сервисе; `null` — `int()` упадёт")
    diverges: bool = Field(description="C- и Python-сервис видят разное (или один из них падает)")
    issue: IssueName = Field(description="`ok`; `missing` — не задана; `no_digits` — atoi вернёт 0; "
                                         "`clamped` — переполнение, прижато к границе; `trailing` — хвост "
                                         "отброшен молча; `out_of_range` — вне `min`…`max`")
    message: str = Field(description="Пояснение для человека")


class AuditResponse(BaseModel):
    findings: list[FindingOut] = Field(description="По одной записи на настройку, в порядке `settings`")
    problems: int = Field(description="Сколько настроек с `issue` ≠ `ok`")


_EXAMPLES = {
    "classic": {
        "summary": "Типичные ошибки в .env",
        "description": "`30s` → 30, `auto` → 0, `4294967296` → 2³¹ − 1, `1_000` → 1 у C и 1000 у Python.",
        "value": {"env": {"WORKERS": "auto", "TIMEOUT_SEC": "30s", "MAX_BODY_BYTES": "4294967296",
                          "BATCH": "1_000", "PORT": "8080"},
                  "settings": [{"name": "WORKERS", "min": 1}, {"name": "TIMEOUT_SEC"},
                               {"name": "MAX_BODY_BYTES"}, {"name": "BATCH"},
                               {"name": "PORT", "bits": 16, "signed": False, "min": 1},
                               {"name": "CACHE_MB", "required": False}]},
    },
    "all_int32": {
        "summary": "Без схемы: все переменные как int32",
        "value": {"env": {"POOL": "16", "RETRIES": " 3 "}},
    },
}


@router.post("/audit", summary="Аудит числовых переменных окружения")
def audit_envconfig(req: Annotated[AuditRequest, Body(openapi_examples=_EXAMPLES)]) -> AuditResponse:
    """Для каждой числовой настройки показывает, что прочитает C-сервис (`atoi`/`strtol`: пробелы → знак →
    цифры до первой не-цифры, прижатие к типу) и что — Python (`int()`), и в чём проблема.

    Ловит тихие ошибки конфигурации: `30s` → 30, `auto` → 0, переполнение типа, расхождение сервисов.
    Алгоритм: **LeetCode 8. String to Integer (atoi)** → `algos.parse_int_prefix`.
    Бизнес-логика: `biz.infra.envconfig`.
    """
    specs = req.settings if req.settings is not None else [SettingIn(name=n) for n in req.env]
    settings = [Setting(s.name, s.bits, s.signed, s.min, s.max, s.required) for s in specs]
    findings = [FindingOut(name=f.name, raw=f.raw, c_value=f.c_value, py_value=f.py_value, diverges=f.diverges,
                           issue=f.issue, message=f.message) for f in audit_env(req.env, settings)]
    return AuditResponse(findings=findings, problems=sum(f.issue != "ok" for f in findings))
