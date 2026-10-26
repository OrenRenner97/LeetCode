"""uv run uvicorn interfaces.api.main:app --reload
   Swagger UI (попробовать): http://127.0.0.1:8000/docs
   ReDoc (читать):           http://127.0.0.1:8000/redoc
   Схема:                    http://127.0.0.1:8000/openapi.json

Как добавить ручку — см. README.md рядом.
"""
from fastapi import FastAPI
from fastapi.routing import APIRoute

from . import errors
from .routers import crypto, fintech, system

API_VERSION = "v1"

DESCRIPTION = """
Задачи LeetCode, превращённые в бизнес-модули. Каждая ручка — тонкая обёртка:

```
HTTP (interfaces.api) → бизнес-логика (biz.<отрасль>) → алгоритм (algos) → python | numpy | numba | C | CUDA
```

* **Версия** в пути: `/v1/...`. Служебные `/health` и `/backends` — без версии.
* **Реализацию алгоритма** можно выбрать полем `backend` (по умолчанию `auto`). Что доступно на сервере — `GET /backends`.
* **Ошибки**: `422` — не прошла валидация схемы, `400` — запрос не выполним (например, backend недоступен).
  Ошибки внутри пакета операций возвращаются в теле ответа, а не HTTP-кодом.
* **Деньги** — только целые числа (копейки) или строки (uint256, токены). Никаких float.
"""

TAGS = [
    {"name": "system", "description": "Служебное: живость сервиса и доступные реализации алгоритмов."},
    {"name": "fintech/reconciliation",
     "description": "Сверка входящих платежей с открытыми счетами. "
                    "Алгоритм: **LeetCode 1. Two Sum** → `algos.find_pair_with_sum`."},
    {"name": "fintech/antifraud",
     "description": "Антифрод: перебор украденных карт (card testing). "
                    "Алгоритм: **LeetCode 3. Longest Substring Without Repeating Characters** → `algos.longest_unique_window`."},
    {"name": "crypto/ledger",
     "description": "Учёт ERC-20-токена на uint256 как в EVM. "
                    "Алгоритм: **LeetCode 2. Add Two Numbers** → `algos.add_digits` / `sum_limbs`."},
]


def _operation_id(route: APIRoute) -> str:
    # operationId = имя функции: стабильно и читаемо в сгенерированных клиентах (openapi-generator и т.п.).
    return route.name


app = FastAPI(
    title="LeetCode++ API",
    version="0.2.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    generate_unique_id_function=_operation_id,
)
errors.install(app)

app.include_router(system.router)
app.include_router(fintech.router, prefix=f"/{API_VERSION}")
app.include_router(crypto.router, prefix=f"/{API_VERSION}")
