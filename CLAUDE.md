# LeetCode++

Решаем задачи LeetCode на Python и доводим каждую до библиотеки, бизнес-модуля, API и ускорения. Общаемся на русском.

## Шаги для каждой задачи (по одному за раз, с остановкой и обсуждением после каждого)

1. **Альтернативы**: классы с тем же методом, что у `Solution`, в `problems/NNNN_slug/alternatives.py` (`ALL = {...}`) + бенчмарк `benchmarks/<slug>.py` + разбор trade-off'ов.
1.5. **Библиотека**: нормальный API (контракт, валидация, `None` вместо гарантий) в `src/algos/<техника>/`, тесты в `tests/algos/`.
2. **Бизнес-кейс**: `src/biz/<отрасль>/<модуль>/` (зависит только от `algos`) + `demo.py` + тесты; по возможности ручка в API.
3. **Скорость**: `src/algos/_native/` + `native/c/` → `register_optional(..., min_n=...)`; бенчмарк `benchmarks/<slug>_backends.py`; `priority`/`min_n` только по замерам.

## Рабочий процесс

1. Пользователь пишет решение в `tmp.py` и говорит «решил». **Решение за пользователя не пишем.**
2. Перед перезаписью `tmp.py` сверяем его с сохранённым `solution.py`.
3. `solution.py` = копия `tmp.py` **без изменений**; замечания пишутся в README задачи.

## Документация обязательна (на всех уровнях)

Каждое изменение обновляет соответствующие README и индексы:
- `problems/NNNN_slug/README.md` (по `templates/problem/README.md`) + строка в `problems/README.md` и `PROGRESS.md`;
- новая функция → строка в индексе `src/algos/README.md`;
- новый бизнес-модуль → свой `README.md` + строка в индексе `src/biz/README.md`;
- новая ручка → таблица в `src/interfaces/api/README.md`; тег с описанием в `TAGS`; `summary`, docstring, `description` у полей, `openapi_examples` у POST (проверяет `tests/interfaces/test_openapi_docs.py`);
- новый C-файл → таблица в `native/README.md`; новый бенчмарк → `benchmarks/README.md`;
- урок из замеров → «Уроки» в `src/algos/_native/README.md`.

## Архитектура

- Слои: `interfaces.api` → `biz` → `algos` → `algos._native`. Импорты только вниз.
- `biz` не знает про numpy/numba/C/GPU: передаёт `backend: str | None`.
- Backend: аргумент → `ALGOS_BACKEND` → `auto` (`priority` + `min_n` у `Dispatcher`).
- `algos` — по технике (`hashing`, `arithmetic`, ...), `biz` — по отраслям (`fintech`, `crypto`, ...).
- API: `routers/<отрасль>/<модуль>.py`, путь `/v1/<отрасль>/...`, тег `<отрасль>/<модуль>`, `operationId` = имя функции, деньги — int-копейки или строки.

## Команды

- `uv sync --all-extras && make -C native` — окружение; `uv run pytest` — все тесты.
- `uv run uvicorn interfaces.api.main:app --reload` → `/docs`, `/redoc`.
- В `addopts` уже стоит `-q`: для итоговой строки используйте `uv run pytest | tail -1`.
