# LeetCode++

Решаем LeetCode и доводим каждую задачу до «настоящего» кода:

```
задача ──► альтернативы ──► библиотека ──► бизнес-модуль ──► HTTP API
 (тренировка)  (шаг 1)        (шаг 1.5)       (шаг 2)          (interfaces)
                                  │
                                  └──► ускорение: numpy / numba / C / CUDA (шаг 3)
```

Прогресс по задачам: **[PROGRESS.md](PROGRESS.md)**

## Карта репозитория

| Папка | Что там | Зачем | README |
|-------|---------|-------|--------|
| `tmp.py` | черновик текущей задачи | сюда пишешь решение | — |
| `problems/NNNN_slug/` | твоё решение, альтернативы, разбор с бенчмарками | учебный журнал: «как я думал» | [problems/](problems/README.md) |
| `src/algos/` | библиотека алгоритмов, разложенная по технике | переиспользуемое ядро с нормальным API | [algos/](src/algos/README.md) |
| `src/algos/_native/` | numpy / numba / ctypes / CuPy-реализации | шаг 3: скорость | [_native/](src/algos/_native/README.md) |
| `native/` | исходники на C + Makefile | то, что компилируется в `libalgos.so` | [native/](native/README.md) |
| `src/biz/<отрасль>/<модуль>/` | бизнес-модули | шаг 2: зачем алгоритм в жизни | [biz/](src/biz/README.md) |
| `src/interfaces/api/` | FastAPI | тонкая HTTP-обёртка над `biz` | [api/](src/interfaces/api/README.md) |
| `tests/` | тесты `algos`, `biz`, `interfaces` | один тест прогоняет все backend'ы | [tests/](tests/README.md) |
| `benchmarks/` | замеры | откуда взялись пороги `auto` | [benchmarks/](benchmarks/README.md) |
| `templates/problem/` | шаблон README задачи | — | — |

## Слои и правило импортов

```
interfaces.api ──► biz ──► algos ──► algos._native ──► native/ (C), numba, CuPy
```

- Импорты идут **только вниз**. `algos` ничего не знает про бизнес, `biz` ничего не знает про C и GPU.
- `biz` выбирает реализацию одной строкой `backend=...` (или не выбирает: тогда `auto` по бенчмаркам).
- Каждый слой можно тестировать и использовать без верхних.

## Быстрый старт

```bash
uv sync --all-extras          # окружение (api, numba, cupy)
make -C native                # собрать C-библиотеку (без неё просто не будет backend'а "c")
uv run pytest                 # все тесты (~350, ~15 s)

uv run uvicorn interfaces.api.main:app --reload    # http://127.0.0.1:8000/docs  (или /redoc)
uv run python -m biz.fintech.reconciliation.demo
uv run python -m biz.crypto.ledger.demo
```

## Как добавить новую задачу (чек-лист)

1. Решить в `tmp.py` → «решил».
2. `problems/NNNN_slug/`: `solution.py` (без изменений), `alternatives.py` (классы), `test_solution.py`, `README.md` по [шаблону](templates/problem/README.md).
3. **1.5** — функция в `src/algos/<техника>/` + тесты в `tests/algos/` + строка в [индексе algos](src/algos/README.md).
4. **2** — модуль `src/biz/<отрасль>/<модуль>/` с `README.md` + строка в [индексе biz](src/biz/README.md); при желании — ручка в API.
5. **3** — backend'ы в `_native/` + бенчмарк в `benchmarks/` + пороги `min_n` по результатам.
6. Строка в [PROGRESS.md](PROGRESS.md).
