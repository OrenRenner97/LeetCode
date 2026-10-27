# Прогресс

| # | Задача | Сложность | Тема | Лучшее решение | Бизнес-кейс | Лучший ускоритель |
|---|--------|-----------|------|----------------|-------------|-------------------|
| 1 | [Two Sum](problems/0001_two_sum) | Easy | Hash Table | hash one-pass O(n)/O(n) | сверка платежей | numba prange (batch), GPU от 10⁵ (single) |
| 2 | [Add Two Numbers](problems/0002_add_two_numbers) | Medium | Linked List, Math | итеративно с переносом O(max(m,n)) → `algos.add_digits` | uint256-леджер токена (crypto) | numba: carry-select (сложение), carry-save (аудит ×4300) |
| 3 | [Longest Substring Without Repeating Characters](problems/0003_longest_substring_without_repeating_characters) | Medium | Sliding Window, Hash Table | окно с прыжком по последней позиции, O(n) → `algos.longest_unique_window` | антифрод: перебор украденных карт (fintech) | numba prange по источникам (×17–51), потоковый детектор 430k/с |
| 4 | [Median of Two Sorted Arrays](problems/0004_median_of_two_sorted_arrays) | Hard | Binary Search | разрез короткого массива O(log min(m,n)) → `algos.median_of_sorted` (с помощью Cursor, перерешать 2026-11-02) | справедливая цена по площадкам (fintech) | numba для разреза (×3), C для K шардов (×6–12); бизнесу не нужен |
