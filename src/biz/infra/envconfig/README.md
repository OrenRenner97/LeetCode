# infra/envconfig — аудит числовых переменных окружения

## Боль

Числовые настройки сервисов живут в переменных окружения строками: `WORKERS`, `TIMEOUT_SEC`, `MAX_BODY_BYTES`. Человек пишет `TIMEOUT_SEC=30s`, `WORKERS=auto`, `BATCH=1_000`, и дальше всё зависит от того, кто читает:

- **C/C++ (`atoi`, `strtol`)** не падает никогда: `30s` → 30 (суффикс отброшен молча), `auto` → 0 (сервис стартует с нулём воркеров), `4294967296` в int32 → 2147483647, `1_000` → 1.
- **Python (`int()`)** на `30s` и `auto` падает, а `1_000` и `٣` понимает как 1000 и 3.

В смешанном стеке одна переменная даёт два разных значения, и узнают об этом по инциденту, а не при деплое.

## Связь с задачей

Разбор, который делает C-сервис, — это ровно **LeetCode 8. String to Integer (atoi)**: пробелы → знак → цифры до первой не-цифры → прижатие к типу. Библиотечная версия `algos.parse_int_prefix` возвращает то, чего нет в LeetCode и что нужно для аудита:

- `None` вместо 0 на мусоре — отличить `auto` от `0`;
- `end` — где кончился разбор: `raw[end:]` и есть молча отброшенный хвост;
- `clamped` — было ли переполнение типа.

## Что есть

- `Setting(name, bits=32, signed=True, min=None, max=None, required=True)` — переменная, тип в C-сервисе и допустимый по смыслу диапазон.
- `check(setting, raw)` → `Finding(name, raw, c_value, py_value, issue, message)`, `diverges` — видят ли C и Python разное.
- `audit_env(env, settings)` — по всему окружению (например, `os.environ`).
- `issue` по убыванию серьёзности: `missing`, `no_digits`, `clamped`, `trailing`, `out_of_range`, `ok`.

## Результат (`python -m biz.infra.envconfig.demo`)

| Переменная | Значение | C (atoi) | Python (int) | Проблема |
|---|---|---|---|---|
| WORKERS | `auto` | 0 | ошибка | no_digits |
| TIMEOUT_SEC | `30s` | 30 | ошибка | trailing |
| MAX_BODY_BYTES | `4294967296` | 2147483647 | 4294967296 | clamped |
| BATCH | `1_000` | 1 | 1000 | trailing |
| RETRIES (uint8) | `-1` | 0 | −1 | clamped |
| PORT (uint16) | `" 8080\n"` | 8080 | 8080 | ok |

## Ограничения (честно)

- **Модель C-разбора — `strtol` + проверка в тип с прижатием.** Настоящий `atoi` при переполнении — UB, `strtoul("-1")` даёт не 0, а `ULONG_MAX` (обёртка). Аудит показывает, что сервис *должен* увидеть при аккуратном коде, и в любом случае помечает строку как проблемную.
- Только десятичные целые. `0x10`, `1e3`, `1.5`, `10MB` → `trailing`: так их и видит `atoi`.

## Как запустить

```bash
uv run python -m biz.infra.envconfig.demo
uv run pytest tests/biz/infra/test_envconfig.py
```

API: `POST /v1/infra/envconfig/audit` — см. [`interfaces/api`](../../../interfaces/api/README.md).
