# crypto/ledger — учёт токена на uint256

**Боль.** Балансы в Ethereum хранятся в `uint256` в минимальных единицах: 1 ETH = 10¹⁸ wei. В int64 помещается ~9.2 ETH, а float теряет wei. Бэкенд биржи, кошелька или индексатора должен считать в 256 битах и вести себя как смарт-контракт: переполнение — это ошибка, а не «большое число».

**Алгоритм.** [LeetCode 2. Add Two Numbers](../../../../problems/0002_add_two_numbers/README.md): `UInt256` — это 4 «цифры» по 64 бита, младшая первой. Сложение — `algos.add_digits(base=2**64)`, вычитание — `sub_digits`, аудит — `sum_limbs` (carry-save).

## Файлы

| Файл | Что |
|------|-----|
| `uint256.py` | `UInt256` (`+`, `-`, сравнение, `hex()`), `Uint256Overflow` / `Underflow`, `parse_units` / `format_units` |
| `ledger.py` | `Ledger` (ERC-20: `mint`, `burn`, `transfer`, события `Transfer`, `audit()`), `audit_balances()` без состояния |
| `demo.py` | выпуск, переводы, нехватка баланса, переполнение 2²⁵⁶ |

## Правила (как в EVM)

- **Проверяемая арифметика**: выход за 2²⁵⁶ − 1 или ниже 0 даёт исключение (в Solidity ≥ 0.8 это `panic 0x11`).
- **Атомарность**: сначала считаются все новые значения, потом записываются. При ошибке состояние не меняется (`revert`).
- **Инвариант**: Σ балансов == `total_supply`, проверяется `audit()`.
- **Суммы только строками** (`parse_units("1.5", 18)`); float даёт `TypeError`.
- `mint` и `transfer` на нулевой адрес запрещены; адреса приводятся к нижнему регистру (EIP-55 checksum не проверяется).

## Почему лимбы, если в Python int бесконечный

1. Нужна точная семантика EVM: потолок 2²⁵⁶.
2. Фиксированные лимбы — **формат для векторизации**: N балансов = массив `(N, 4) uint64`. Аудит 10⁷ балансов через `sum_limbs` (numba) занимает ~40 ms. Сложение `UInt256` по одному потребовало бы минуты.
3. Сами `UInt256` (4 лимба) складываются на Python: до ~256 лимбов вызов нативного кода дороже, чем работа.

```bash
uv run python -m biz.crypto.ledger.demo
uv run pytest tests/biz/crypto
```

API ([`routers/crypto/ledger.py`](../../../interfaces/api/routers/crypto/ledger.py)):
`POST /v1/crypto/ledger/simulate`, `POST /v1/crypto/ledger/audit`, `GET /v1/crypto/units/parse|format`.
В JSON все суммы — строки: число в JavaScript точно только до 2⁵³.

**Куда развивать:** `approve` / `transferFrom`, умножение и деление uint256 (комиссии, курсы), индексатор, который восстанавливает балансы из журнала событий блокчейна.
