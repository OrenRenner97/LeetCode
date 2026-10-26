# fintech/reconciliation — сверка платежей

**Боль.** Клиент одним переводом оплачивает сразу два счёта, а в назначении пишет «оплата по договору». Бухгалтер вручную подбирает, какие счета закрыть.

**Алгоритм.** [LeetCode 1. Two Sum](../../../../problems/0001_two_sum/README.md): `target` — сумма платежа, `values` — открытые счета клиента. Вызов: `algos.find_pair_with_sum`.

## Правила `Reconciler`

1. Платёж = один счёт → закрыть его (проверяется первым, самый частый случай).
2. Платёж = сумма двух счетов → закрыть оба.
3. Иначе → `UNMATCHED`, ручной разбор (частичная оплата, переплата, опечатка).

## Бизнес-детали

- Деньги в **копейках** (`int`): во `float` сравнение на равенство ненадёжно.
- Закрытый счёт удаляется из открытых, и второй раз его не оплатить.
- Счета перебираются **по сроку оплаты**: `find_pair_with_sum` возвращает пару с минимальным `j`, поэтому первыми закрываются самые старые долги.
- Ищем только среди счетов **этого клиента** (`customer_id` берётся по ИНН из выписки).

## Файлы

| Файл | Что |
|------|-----|
| `models.py` | `Invoice`, `Payment`, `Match`, `MatchKind`, `Report` |
| `reconciler.py` | `Reconciler(backend=None)`: `add_invoices`, `reconcile`, `run` |
| `demo.py` | 12 платежей → 4 одним счётом, 4 парой, 4 на ручной разбор |

```bash
uv run python -m biz.fintech.reconciliation.demo [--backend python]
uv run pytest tests/biz/fintech
```

API: `POST /v1/fintech/reconcile` ([`routers/fintech/reconciliation.py`](../../../interfaces/api/routers/fintech/reconciliation.py)).

**Масштаб:** для ночной сверки тысяч клиентов есть `algos.find_pairs_batch` (numba `prange`, до ×70 к Python), см. [разбор задачи 1](../../../../problems/0001_two_sum/README.md).
**Куда развивать:** сумма из k счетов (Subset Sum; при малых k — meet-in-the-middle), допуск ±N копеек на комиссии, нечёткое сопоставление по назначению платежа.
