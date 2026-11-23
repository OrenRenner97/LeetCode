# algos — библиотека алгоритмов

Лучшие решения задач, переделанные из «формата LeetCode» в нормальный API: чёткий контракт, валидация, `None` вместо «ответ гарантирован», выбор реализации.

## Индекс

| Функция | Модуль | Из задачи | Что делает | Сложность | Backend'ы |
|---------|--------|-----------|------------|-----------|-----------|
| `find_pair_with_sum(values, target)` | `hashing/pair_sum.py` | [1. Two Sum](../../problems/0001_two_sum/README.md) | индексы пары с суммой `target` или `None` | O(n) | python, numpy, numba, c, cuda |
| `find_pairs_batch(values, offsets, targets)` | `hashing/pair_sum_batch.py` | 1. Two Sum | много независимых Two Sum за один вызов (формат CSR) | O(n) | python, numpy, numba, cuda |
| `add_digits(a, b, base=10)` | `arithmetic/digits.py` | [2. Add Two Numbers](../../problems/0002_add_two_numbers/README.md) | длинное сложение массивов цифр, любое основание | O(n) | python, numpy, numba, c, cuda |
| `sub_digits(a, b, base=10)` | `arithmetic/digits.py` | 2. Add Two Numbers | длинное вычитание (a ≥ b) | O(n) | python |
| `sum_limbs(rows, base=2**64)` | `arithmetic/sum_limbs.py` | 2. Add Two Numbers | сумма N длинных чисел, carry-save | O(N·L) | python, numpy, numba, cuda |
| `to_digits(n, base)` / `from_digits(d, base)` | `arithmetic/digits.py` | 2. Add Two Numbers | int ↔ цифры | O(n²) | — |
| `reverse_digits(x, base=10, width=None, bits=None, signed=True)` | `arithmetic/reverse.py` | [7. Reverse Integer](../../problems/0007_reverse_integer/README.md) | цифры в обратном порядке; `width` — в фиксированной ширине (обратимо); не влезает в `bits` бит → `None` | O(d) | — |
| `parse_int_prefix(s, base=10, bits=32, signed=True, whitespace=" ")` | `parsing/atoi.py` | [8. String to Integer (atoi)](../../problems/0008_string_to_integer_atoi/README.md) | целое с начала строки как `strtol`: `IntPrefix(value, end, clamped)`, нет цифр → `None`; любое основание, прижатие к `bits` бит | O(n) | — |
| `int_range(bits, signed=True)` | `arithmetic/reverse.py` | 7. Reverse Integer | границы целого на `bits` бит: `(−2³¹, 2³¹ − 1)` | O(1) | — |
| `is_digit_palindrome(x, base=10, width=None)` | `arithmetic/palindrome.py` | [9. Palindrome Number](../../problems/0009_palindrome_number/README.md) | палиндром по цифрам; отрицательные — нет; `width` — с ведущими нулями («0110») | O(d) | — |
| `next_digit_palindrome(x, base=10)` / `prev_digit_palindrome(x, base=10)` | `arithmetic/palindrome.py` | 9. Palindrome Number | ближайший палиндром ≥ x / ≤ x отражением левой половины; `prev` для x < 0 → `None` | O(d) | — |
| `compile_pattern(pattern, escape="\\")` / `is_match(s, pattern, escape="\\")` | `automata/simple_regex.py` | [10. Regular Expression Matching](../../problems/0010_regular_expression_matching/README.md) | шаблоны `.` и `x*` на всю строку, линейно на любом входе (НКА, состояния — битовая маска, без ReDoS); экранирование `\.`; `SimplePattern.from_tokens` — любые последовательности; `start`/`step`/`accepts` — пошагово по потоку | O(len(s) · k / w) | — |
| `max_container(heights, xs=None, min_width=0)` | `two_pointers/container.py` | [11. Container With Most Water](../../problems/0011_container_with_most_water/README.md) | пара линий с максимальной площадью `(x[j] − x[i]) · min(h)`: `Container(left, right, area)` или `None`; произвольные координаты, минимальная ширина | O(n) | — |
| `to_roman(n, lowercase=False)` | `arithmetic/roman.py` | [12. Integer to Roman](../../problems/0012_integer_to_roman/README.md) | каноническая римская запись; вне `[ROMAN_MIN, ROMAN_MAX]` = [1, 3999] → `None` (нет символа для 5000, MMMM не канонично); `lowercase` — строчные; таблица всех ответов при импорте | O(1) | — |
| `from_roman(s)` | `arithmetic/roman.py` | [13. Roman to Integer](../../problems/0013_roman_to_integer/README.md) | строгий разбор: только каноническая запись (как у `to_roman`), иначе `None` (`IIII`, `IC`, `MMMM`, смешанный регистр); верхний или нижний регистр | O(len(s)) | — |
| `longest_unique_window(seq, max_repeats=1)` | `sliding_window/unique_window.py` | [3. Longest Substring…](../../problems/0003_longest_substring_without_repeating_characters/README.md) | `[start, end)` самого длинного окна, где каждый элемент встречается ≤ k раз | O(n) | python, numba, c, numpy, cuda |
| `longest_unique_window_batch(values, offsets, max_repeats=1)` | `sliding_window/unique_window_batch.py` | 3. Longest Substring… | то же для многих последовательностей сразу (CSR) | O(n) | python, numba, numpy, cuda |
| `median_of_sorted(*arrays)` | `binary_search/sorted_union.py` | [4. Median of Two Sorted Arrays](../../problems/0004_median_of_two_sorted_arrays/README.md) | медиана объединения отсортированных последовательностей без слияния; пусто → `None` | O(log min(m,n)) для 1–2, O(k·log n·log R) для 3+ | numba, c, python (нативные — только для int-массивов numpy) |
| `kth_of_sorted(*arrays, k)` | `binary_search/sorted_union.py` | 4. Median of Two Sorted Arrays | k-й элемент (перцентиль) объединения: сам выбирает разрез или бинпоиск по значению | как у `median_of_sorted` | как у `median_of_sorted` |
| `kth_of_two_sorted(a, b, k)` | `binary_search/sorted_union.py` | 4. Median of Two Sorted Arrays | k-й элемент объединения двух, любые сравнимые типы | O(log min(m,n)) | numba, c, python |
| `kth_of_many_sorted(arrays, k)` | `binary_search/sorted_union.py` | 4. Median of Two Sorted Arrays | k-й элемент объединения k последовательностей целых (бинпоиск по значению) | O(k·log n·log R) | c, numba, python |
| `longest_palindrome(seq, mirror=None)` | `palindromes/manacher.py` | [5. Longest Palindromic Substring](../../problems/0005_longest_palindromic_substring/README.md) | `[start, end)` самого длинного (самого левого) палиндрома; `mirror` — палиндром с отображением (ДНК-комплемент); нет → `None` | O(n) | numba, c, python (нативные — строки и int-массивы) |
| `palindrome_radii(seq, mirror=None)` | `palindromes/manacher.py` | 5. Longest Palindromic Substring | массив Manacher: длина максимального палиндрома на каждом из 2n + 1 центров | O(n) | numba, c, python |
| `maximal_palindromes(seq, min_length=2, mirror=None)` | `palindromes/manacher.py` | 5. Longest Palindromic Substring | все максимальные палиндромы длины ≥ `min_length`, по одному на центр | O(n + k log k) | numba, c, python |
| `zigzag_encode(seq, rows, mode="zigzag")` | `permutations/zigzag.py` | [6. Zigzag Conversion](../../problems/0006_zigzag_conversion/README.md) | зигзаг-перестановка (построчное чтение), тип результата = тип входа; `mode="snake"` — края дважды (snake-драфт) | O(n) при любом `rows` | python |
| `zigzag_decode(seq, rows, mode="zigzag")` | `permutations/zigzag.py` | 6. Zigzag Conversion | обратная перестановка: `decode(encode(x)) == x` | O(n) | python |
| `zigzag_rows(n, rows, mode="zigzag")` / `zigzag_order(n, rows, mode="zigzag")` | `permutations/zigzag.py` | 6. Zigzag Conversion | номер строки каждой позиции / перестановка индексов | O(n) | — |
| `zigzag_split(seq, rows, mode="zigzag")` | `permutations/zigzag.py` | 6. Zigzag Conversion | сами строки: раздача по `rows` корзинам змейкой | O(n + rows) | — |

Импорт: `from algos import find_pair_with_sum, add_digits` или `from algos.arithmetic import sum_limbs`.

## Как устроено

**Раскладка по технике, а не по номеру задачи** (`hashing/`, `arithmetic/`, `automata/`, `sliding_window/`, `two_pointers/`, `binary_search/`, `palindromes/`, `permutations/`, позже `graphs/`, `dp/`). Одна техника решает десятки задач, и родственные функции оказываются рядом.

**Выбор реализации — `_dispatch.py`:**

```python
_dispatch = Dispatcher("add_digits", priority=("numba", "c", "numpy", "cuda", "python"))

@_dispatch.register("python")                       # эталон: есть всегда
def _python(a, b, base): ...

_dispatch.register_optional("numba", "algos._native.numba_impl", "add_digits_numba", min_n=256)
```

- `resolve(backend, n)`: явный `backend=` → переменная `ALGOS_BACKEND` → `auto` (первая доступная по `priority`, у которой `min_n <= n`).
- `register_optional` **не падает**, если модуль не импортируется (нет numba, не собран `.so`, нет GPU): backend просто не появится. Причина видна в `_dispatch.import_errors`.
- `priority` и `min_n` **берутся из бенчмарков**, а не из интуиции. Рядом с `Dispatcher(...)` всегда комментарий со ссылкой на бенчмарк.
- `func.backends` — список доступных реализаций на этой машине. По нему параметризуются тесты.

## Правила для новой функции

1. **Контракт в docstring**: что возвращает, что при отсутствии ответа, тип результата, ограничения нативных backend'ов (например, «|values| < 2^62»).
2. **Python-реализация обязательна** — это эталон, и она работает везде.
3. **Валидация в публичной функции**, а не в backend'ах: она одна на всех. Для numpy-массивов проверка должна быть векторной, иначе цикл на Python съест выигрыш.
4. **Тип результата = тип входа** (list → list, ndarray → ndarray), если для функции это имеет смысл.
5. Тесты в `tests/algos/` параметризуются по `func.backends`: один тест проверяет все реализации.
6. Строка в индексе выше.

## Как добавить backend

См. [`_native/README.md`](_native/README.md).
