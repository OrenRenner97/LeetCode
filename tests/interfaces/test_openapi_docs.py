"""Линтер документации API: новая ручка без описания или примеров уронит тесты.

Правила (см. src/interfaces/api/README.md):
  - у каждой операции есть тег из TAGS (с описанием), summary и развёрнутый description;
  - operationId уникален (это имя функции — его увидят сгенерированные клиенты);
  - бизнес-ручки живут под /v1/...;
  - у POST есть хотя бы один пример тела запроса (openapi_examples);
  - у каждого поля наших схем есть description.
"""
import pytest

pytest.importorskip("fastapi")

from interfaces.api.main import API_VERSION, app  # noqa: E402

SPEC = app.openapi()
OPS = [(path, method, op) for path, ops in SPEC["paths"].items() for method, op in ops.items()]
FASTAPI_BUILTIN_SCHEMAS = {"HTTPValidationError", "ValidationError"}


def _id(p):
    return f"{p[1].upper()} {p[0]}"


@pytest.mark.parametrize("path, method, op", OPS, ids=[_id(p) for p in OPS])
def test_operation_documented(path, method, op):
    declared = {t["name"]: t for t in SPEC["tags"]}
    assert op.get("tags"), "нет тега"
    for t in op["tags"]:
        assert t in declared, f"тег {t!r} не объявлен в TAGS (main.py)"
        assert len(declared[t].get("description", "")) > 20, f"у тега {t!r} нет описания"
    assert op.get("summary"), "нет summary"
    assert len(op.get("description", "")) >= 40, "нет развёрнутого description (docstring функции)"
    if op["tags"] != ["system"]:
        assert path.startswith(f"/{API_VERSION}/"), "бизнес-ручки — только под версией"
    if method == "post":
        content = op["requestBody"]["content"]["application/json"]
        assert content.get("examples"), "у POST нет примеров тела (Body(openapi_examples=...))"


def test_operation_ids_unique():
    ids = [op["operationId"] for _, _, op in OPS]
    assert len(ids) == len(set(ids)), "operationId (имена функций) должны быть уникальны"


SCHEMAS = {k: v for k, v in SPEC["components"]["schemas"].items() if k not in FASTAPI_BUILTIN_SCHEMAS}


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_fields_described(name):
    props = SCHEMAS[name].get("properties", {})
    undocumented = [p for p, s in props.items() if "description" not in s and "$ref" not in s]
    assert not undocumented, f"{name}: поля без description: {undocumented}"
