# tests/

Структура повторяет `src/`: `tests/algos/` ↔ `src/algos/`, `tests/biz/<отрасль>/` ↔ `src/biz/<отрасль>/`, `tests/interfaces/` ↔ `src/interfaces/`.
Тесты учебных решений лежат рядом с ними: `problems/*/test_solution.py`.

```bash
uv run pytest                              # всё (~350 тестов, ~15 s)
uv run pytest tests/algos                  # только библиотека
uv run pytest -k cuda                      # только GPU-варианты
uv run pytest tests/interfaces/test_openapi_docs.py   # линтер документации API
```

## Приёмы

**Один тест на все backend'ы.** Фикстура параметризуется списком реализаций, доступных на этой машине:

```python
@pytest.fixture(params=add_digits.backends)
def backend(request):
    return request.param

def test_contract(backend): ...           # прогонится для python, numpy, numba, c, cuda
```

Нет GPU — нет `cuda` в списке, тест просто не создаётся (не skip и не fail).

**Эталон.** Случайные тесты сравнивают с заведомо верным: Python `int` для длинной арифметики, brute force для Two Sum, «теневой» словарь на int для леджера.

**Худшие случаи для параллельного кода.** Цепочки переноса через весь массив (`999…9 + 1`) на размерах больше порога, где numba режет данные на куски. Иначе ошибка на границе кусков останется незамеченной.

**Атомарность.** Для бизнес-операций проверяем, что после исключения состояние **не изменилось**.

**Линтер документации API** (`interfaces/test_openapi_docs.py`): у каждой ручки тег из `TAGS`, `summary`, `description`, у POST есть примеры, у каждого поля схем есть `description`.
