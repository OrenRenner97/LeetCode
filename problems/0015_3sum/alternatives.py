"""15. 3Sum: альтернативные решения.

n — длина массива, u — число различных значений (u ≤ n), t — число троек в ответе.

| # | Класс                  | Время         | Память | Идея                                                                          |
|---|------------------------|---------------|--------|-------------------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(n³)         | O(t)   | все тройки индексов, дубликаты — через set отсортированных кортежей            |
| 1 | Combinations           | O(n³)         | O(t)   | тот же перебор, но по отсортированному массиву через itertools.combinations    |
| 2 | SortTwoPointers        | O(n²)         | O(1)   | сортировка; фиксируем a, пару ищем двумя указателями; дубликаты — пропуском    |
| 3 | SortHashSet            | O(n²)         | O(n)   | сортировка; фиксируем a, пару ищем как в Two Sum через set                     |
| 4 | CounterValues          | O(n + u²)     | O(u)   | Counter по значениям; перебор пар различных a ≤ b, c = −a−b ≥ b ищем в Counter |
| 5 | SignSplit              | O(n²) худш.   | O(n)   | отрицательные / нули / положительные: тройка — это 0 ± p или пара одного знака + одно другого |
| 6 | NumpySearchsorted      | O(n² log n)   | O(n)   | numpy: для каждого a сразу все c = −a−b через searchsorted по отсортированному массиву |
"""
from collections import Counter
from itertools import combinations

import numpy as np


class Combinations:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # Перебор остаётся кубическим, но цикл — в C (itertools), а сортировка заранее
        # делает каждую тройку уже упорядоченной: sorted() на каждую найденную не нужен.
        return [list(t) for t in {t for t in combinations(sorted(nums), 3) if sum(t) == 0}]


class SortTwoPointers:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # После сортировки для фиксированного a пара (b, c) с b + c = −a ищется за O(n):
        # сумма мала — двигаем l вправо (nums[l] не подходит ни с каким r, все c левее ещё меньше),
        # велика — r влево. Одинаковые значения пропускаем — дубликатов не возникает вовсе.
        nums = sorted(nums)
        n = len(nums)
        res = []
        for i in range(n - 2):
            a = nums[i]
            if a > 0:                           # дальше все три положительные
                break
            if i and a == nums[i - 1]:          # то же a уже было
                continue
            l, r = i + 1, n - 1
            while l < r:
                s = a + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([a, nums[l], nums[r]])
                    l += 1
                    r -= 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
                    while l < r and nums[r] == nums[r + 1]:
                        r -= 1
        return res


class SortHashSet:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # Свели к Two Sum (задача 1): для фиксированного a ищем b + c = −a, видимые b храним в set.
        # Сортировка нужна только для дедупликации: тройка (a, b, c) выходит уже упорядоченной.
        nums = sorted(nums)
        n = len(nums)
        res = set()
        for i in range(n - 2):
            a = nums[i]
            if a > 0:
                break
            if i and a == nums[i - 1]:
                continue
            seen = set()
            for c in nums[i + 1:]:
                b = -a - c
                if b in seen:
                    res.add((a, b, c))
                seen.add(c)
        return [list(t) for t in res]


class CounterValues:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # Ответ зависит только от значений и их кратностей. Перебираем пары различных значений a ≤ b
        # и проверяем c = −a − b ≥ b по счётчику; кратность нужна, когда значения совпадают.
        # Работает за O(u²): при сильно повторяющихся данных u ≪ n.
        cnt = Counter(nums)
        vals = sorted(cnt)
        res = []
        for i, a in enumerate(vals):
            if a > 0:
                break
            for b in vals[i:]:
                c = -a - b
                if c < b:
                    break                       # b растёт, c убывает — дальше только c < b
                if c not in cnt:
                    continue
                if a == b == c:                 # только 0, нужен трижды
                    ok = cnt[a] >= 3
                elif a == b:
                    ok = cnt[a] >= 2
                elif b == c:
                    ok = cnt[b] >= 2
                else:
                    ok = True
                if ok:
                    res.append([a, b, c])
        return res


class SignSplit:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # Сумма трёх = 0 возможна только так: (0, 0, 0); (−p, 0, p); два отрицательных + один положительный;
        # два положительных + один отрицательный. Пары перебираются внутри одной группы знака,
        # третье число ищется в set другой — групп меньше n, а пар одного знака меньше, чем всех.
        neg = [x for x in nums if x < 0]
        pos = [x for x in nums if x > 0]
        zeros = len(nums) - len(neg) - len(pos)
        neg_set, pos_set = set(neg), set(pos)
        res = set()
        if zeros >= 3:
            res.add((0, 0, 0))
        if zeros:
            for p in pos_set:
                if -p in neg_set:
                    res.add((-p, 0, p))
        for i in range(len(neg)):
            for j in range(i + 1, len(neg)):
                c = -(neg[i] + neg[j])
                if c in pos_set:
                    x, y = sorted((neg[i], neg[j]))
                    res.add((x, y, c))
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                c = -(pos[i] + pos[j])
                if c in neg_set:
                    x, y = sorted((pos[i], pos[j]))
                    res.add((c, x, y))
        return [list(t) for t in res]


class NumpySearchsorted:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        # Для каждого различного a (n шагов Python) векторно: b пробегает s[i+1:], c = −a − b,
        # его индекс в s ищем searchsorted'ом и проверяем «нашёлся и стоит правее b».
        # Дубликаты пар убираем np.unique по строкам. Внутренний цикл — в C, но с log n на поиск.
        s = np.sort(np.asarray(nums, dtype=np.int64))
        n = len(s)
        parts = []
        for i in range(n - 2):
            a = s[i]
            if a > 0:
                break
            if i and a == s[i - 1]:
                continue
            j = np.arange(i + 1, n - 1)
            b = s[j]
            c = -a - b
            k = np.searchsorted(s, c, side="right") - 1     # последнее вхождение c
            ok = (k > j) & (s[np.clip(k, 0, n - 1)] == c)
            if ok.any():
                bs = b[ok]
                parts.append(np.column_stack([np.full(len(bs), a), bs, c[ok]]))
        if not parts:
            return []
        return np.unique(np.concatenate(parts), axis=0).tolist()


ALL = {
    "Combinations": Combinations,
    "SortTwoPointers": SortTwoPointers,
    "SortHashSet": SortHashSet,
    "CounterValues": CounterValues,
    "SignSplit": SignSplit,
    "NumpySearchsorted": NumpySearchsorted,
}
