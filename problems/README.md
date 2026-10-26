# problems/ — учебный журнал

Одна папка = одна задача LeetCode. Здесь код **в формате LeetCode** (класс `Solution`) и разбор: как решал, какие есть альтернативы, сколько они стоят. Переиспользуемый код живёт не здесь, а в [`src/algos`](../src/algos/README.md).

Сводная таблица всех задач — [PROGRESS.md](../PROGRESS.md).

## Что лежит в папке задачи

| Файл | Что | Правило |
|------|-----|---------|
| `solution.py` | твоё решение из `tmp.py` | **не редактируется**: замечания пишутся в README |
| `alternatives.py` | другие подходы, классы с тем же методом, что у `Solution` | словарь `ALL = {"Имя": Класс}` в конце |
| `test_solution.py` | примеры, краевые случаи, случайные тесты: все реализации против эталона | запускается и без pytest: `python3 test_solution.py` |
| `README.md` | условие → разбор решения → шаги 1, 1.5, 2, 3 с таблицами замеров | по [шаблону](../templates/problem/README.md) |

## Почему так

- **Решение не трогаем**, чтобы видеть свой прогресс. Через 50 задач интересно смотреть, как менялся стиль.
- **Альтернативы — это классы с тем же интерфейсом**: один тест и один бенчмарк покрывают все сразу.
- **Имена файлов во всех задачах одинаковые.** Чтобы Python не подсунул `solution.py` от соседней задачи, [`conftest.py`](conftest.py) сбрасывает кэш модулей перед каждой папкой.

## Задачи

| # | Задача | Техника | Библиотека | Бизнес |
|---|--------|---------|------------|--------|
| 1 | [Two Sum](0001_two_sum/README.md) | хэш-таблица | `algos.find_pair_with_sum`, `find_pairs_batch` | [сверка платежей](../src/biz/fintech/reconciliation/README.md) |
| 2 | [Add Two Numbers](0002_add_two_numbers/README.md) | сложение с переносом | `algos.add_digits`, `sub_digits`, `sum_limbs` | [uint256-леджер](../src/biz/crypto/ledger/README.md) |
| 3 | [Longest Substring Without Repeating Characters](0003_longest_substring_without_repeating_characters/README.md) | скользящее окно | `algos.longest_unique_window` | [антифрод: card testing](../src/biz/fintech/antifraud/README.md) |
