# interfaces/api — HTTP API (FastAPI)

Тонкая обёртка над [`biz`](../../biz/README.md): принять JSON → вызвать бизнес-логику → вернуть JSON. **Бизнес-логики здесь нет.**

```bash
uv run uvicorn interfaces.api.main:app --reload
```

- http://127.0.0.1:8000/docs — Swagger UI: попробовать ручки, примеры уже подставлены;
- http://127.0.0.1:8000/redoc — ReDoc: удобно читать;
- http://127.0.0.1:8000/openapi.json — схема (для генерации клиентов).

## Структура

| Файл | Что |
|------|-----|
| `main.py` | приложение: общее описание (`DESCRIPTION`), **теги с описаниями** (`TAGS`), подключение роутеров, версия `/v1` |
| `routers/<отрасль>/__init__.py` | роутер отрасли (`prefix="/<отрасль>"`), собирает модули |
| `routers/<отрасль>/<модуль>.py` | ручки одного модуля из `biz/<отрасль>/<модуль>`; тег = `<отрасль>/<модуль>` |
| `routers/system.py` | `/health`, `/backends` |
| `schemas.py` | общие типы полей (например, `Backend`) |
| `errors.py` | единый формат ошибок `{"detail": ...}`, обработчики, описания кодов для OpenAPI |

## Ручки

| Метод | Путь | Тег | Что |
|-------|------|-----|-----|
| GET | `/health` | system | liveness |
| GET | `/backends` | system | какие реализации алгоритмов есть на сервере |
| POST | `/v1/fintech/reconcile` | fintech/reconciliation | сверка платежей со счетами (Two Sum) |
| POST | `/v1/fintech/antifraud/card-testing` | fintech/antifraud | перебор украденных карт (Longest Substring) |
| POST | `/v1/fintech/fair-price` | fintech/fair_price | справедливая цена по площадкам + контроль нерыночных сделок (Median of Two Sorted Arrays) |
| POST | `/v1/crypto/ledger/simulate` | crypto/ledger | прогон mint/burn/transfer на uint256 |
| POST | `/v1/crypto/ledger/audit` | crypto/ledger | Σ балансов == total_supply (carry-save) |
| GET | `/v1/crypto/units/parse` | crypto/ledger | токены → wei |
| GET | `/v1/crypto/units/format` | crypto/ledger | wei → токены |

## Соглашения

- **Версия в пути** (`/v1/...`) для бизнес-ручек. Ломающее изменение = `/v2`, старая версия живёт параллельно. `/health` и `/backends` без версии.
- **Тег = `<отрасль>/<модуль>`**, объявлен в `TAGS` с описанием и ссылкой на задачу LeetCode и функцию `algos`.
- **`operationId` = имя функции** (`simulate_ledger`): стабильно и читаемо в сгенерированных клиентах. Должно быть уникальным.
- **Ошибки:** `422` — валидация схемы (автоматически), `400` — запрос корректен, но не выполним (недоступный `backend`). Ошибки внутри пакета операций возвращаются в теле (`failed: [...]`), чтобы клиент видел результат целиком.
- **Деньги:** копейки (`int`) или строки (uint256, токены). Не float и не JSON-числа больше 2⁵³.
- **Запросы без состояния:** всё нужное передаётся в теле. Хранилища пока нет.
- **`backend`** — необязательное поле в теле бизнес-ручек (тип `schemas.Backend`).

## Как добавить ручку (чек-лист)

1. Файл `routers/<отрасль>/<модуль>.py` с `router = APIRouter(prefix=..., tags=["<отрасль>/<модуль>"])` и `include_router` в `routers/<отрасль>/__init__.py`. Новая отрасль = новый пакет + `include_router(..., prefix=f"/{API_VERSION}")` в `main.py`.
2. Тег `<отрасль>/<модуль>` в `TAGS` (`main.py`) с описанием.
3. Pydantic-модели: **у каждого поля `description`** (и `examples`, где полезно).
4. Функция-ручка: `summary=` (коротко), docstring (развёрнуто: что делает, какой алгоритм, где бизнес-логика), `responses=BAD_BACKEND`, если есть `backend`.
5. У POST — примеры тела: `Body(openapi_examples={...})`. Они появятся в Swagger в выпадающем списке.
6. Тесты в `tests/interfaces/test_api_<отрасль>.py`.
7. Строка в таблице ручек выше.

Пункты 2–5 проверяет **линтер документации** [`tests/interfaces/test_openapi_docs.py`](../../../tests/interfaces/test_openapi_docs.py): ручка без описания, примеров или с полем без `description` роняет тесты.
