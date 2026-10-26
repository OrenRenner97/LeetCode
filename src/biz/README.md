# biz — бизнес-модули

Ответ на вопрос «зачем этот алгоритм в жизни». Каждый модуль решает настоящую прикладную задачу и использует `algos` как библиотеку.

## Индекс по отраслям

| Отрасль | Модуль | Что решает | Алгоритм | API |
|---------|--------|------------|----------|-----|
| fintech | [reconciliation](fintech/reconciliation/README.md) | сверка платежей со счетами: один платёж закрывает два счёта | 1. Two Sum → `find_pair_with_sum` | `POST /v1/fintech/reconcile` |
| fintech | [antifraud](fintech/antifraud/README.md) | перебор украденных карт (card testing) с одного IP/устройства | 3. Longest Substring… → `longest_unique_window` | `POST /v1/fintech/antifraud/card-testing` |
| crypto | [ledger](crypto/ledger/README.md) | учёт ERC-20-токена на uint256, аудит Σ балансов | 2. Add Two Numbers → `add_digits`, `sum_limbs` | `/v1/crypto/...` |

## Правила

1. **Структура: `biz/<отрасль>/<модуль>/`.** Папку отрасли создаём, только когда появляется первый модуль.
2. **Без фреймворков.** Чистый Python: dataclass'ы, исключения, функции. HTTP, CLI и очереди — это [`interfaces`](../interfaces/api/README.md).
3. **Зависим только от `algos`** (и stdlib). Не импортируем `algos._native`, numpy или numba: реализация выбирается строкой `backend=...`.
4. **Бизнес-детали, которых нет в LeetCode, — главное в модуле**: деньги в целых единицах (копейки, wei), атомарность операций, валидация, приоритеты (старые долги первыми) и т.п.
5. **В модуле есть:** `README.md` (боль → связь с алгоритмом → правила → как запустить), `demo.py` (`python -m biz.<отрасль>.<модуль>.demo`), тесты в `tests/biz/<отрасль>/`.
6. Строка в индексе выше.
