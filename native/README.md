# native/ — исходники на C

Компилируются в одну библиотеку `src/algos/_native/libalgos.so`. Её загружает [`c_impl.py`](../src/algos/_native/c_impl.py) через ctypes.

```bash
make -C native          # сборка (-O3 -march=native)
make -C native clean
```

`.so` не коммитится (`.gitignore`): `-march=native` подстраивает код под конкретный процессор.

| Файл | Функция | Из задачи | Трюк |
|------|---------|-----------|------|
| `c/pair_sum.c` | `pair_sum` | 1. Two Sum | хэш-таблица с открытой адресацией, Fibonacci hashing, ключ и индекс в одной ячейке (один промах кэша на пробу), `calloc` для ленивого обнуления |
| `c/unique_window.c` | `longest_unique_window` | 3. Longest Substring… | LastIndex на массиве по сжатым id (`buf[x]` = позиция + 1, `calloc` = «не встречался»); при k > 1 счётчики |
| `c/sorted_union.c` | `kth_two_i64`, `kth_many_i64` | 4. Median of Two Sorted Arrays | разрез на int64; K массивов — массив указателей + длин, бинпоиск по значению; `upper_bound` **без ветвлений** (cmov), середина `(lo>>1)+(hi>>1)+(lo&hi&1)` без переполнения int64 |
| `c/digits.c` | `add_digits_u64` | 2. Add Two Numbers | `_addcarry_u64`, то есть инструкция ADC: перенос несёт флаг процессора; хвост без переноса копируется `memcpy` |

## Соглашения ABI

- Только простые типы: указатели на `int64_t`/`uint64_t`, длины `int64_t`. Никаких структур через границу.
- Выходные массивы выделяет **Python** (numpy) и передаёт указатель. C не владеет памятью, которую видит Python.
- Код возврата: `1`/`0` — результат, `-1` — ошибка (например, `malloc`). Обёртка превращает его в исключение.
- В Python: `argtypes` с `c_void_p` и передача `arr.ctypes.data`. `data_as()` медленный.
- Новый `.c` в `c/` подхватывается Makefile автоматически.
