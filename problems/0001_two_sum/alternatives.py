"""1. Two Sum: альтернативные решения от худшего к лучшему.

У каждого класса тот же интерфейс, что у Solution на LeetCode: `twoSum(nums, target)`.

| # | Класс                    | Время      | Память | Комментарий                                  |
|---|--------------------------|------------|--------|----------------------------------------------|
| 0 | Solution (solution.py)   | O(n^2)     | O(1)   | n^2 итераций, каждая пара проверяется 2 раза |
| 1 | BruteHalf                | O(n^2)     | O(1)   | j > i, в 2 раза меньше итераций              |
| 2 | SortTwoPointers          | O(n log n) | O(n)   | сортируем индексы, сходимся с двух концов    |
| 3 | HashTwoPass              | O(n)       | O(n)   | сначала строим словарь, потом ищем           |
| 4 | HashOnePass  (оптимум)   | O(n)       | O(n)   | ищем дополнение в уже увиденных              |
"""
from typing import List


class BruteHalf:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Пара (i, j) и (j, i) одна и та же, поэтому достаточно j > i.
        # Заодно исчезает проверка i != j.
        n = len(nums)
        for i in range(n):
            need = target - nums[i]  # вычисляем один раз на внешнюю итерацию
            for j in range(i + 1, n):
                if nums[j] == need:
                    return [i, j]
        return []


class SortTwoPointers:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Сортируем индексы по значению, оригинальные индексы сохраняются.
        # Два указателя: сумма мала → двигаем левый, велика → правый.
        # Каждый шаг отбрасывает элемент, который точно не войдёт в ответ, поэтому проход O(n).
        order = sorted(range(len(nums)), key=nums.__getitem__)
        lo, hi = 0, len(order) - 1
        while lo < hi:
            s = nums[order[lo]] + nums[order[hi]]
            if s == target:
                return [order[lo], order[hi]]
            if s < target:
                lo += 1
            else:
                hi -= 1
        return []


class HashTwoPass:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Проход 1: value -> последний индекс. Проход 2: ищем дополнение.
        # При дубликатах ([3, 3], 6) последний индекс отличается от i, поэтому всё корректно.
        pos = {x: i for i, x in enumerate(nums)}
        for i, x in enumerate(nums):
            j = pos.get(target - x)
            if j is not None and j != i:
                return [i, j]
        return []


class HashOnePass:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Для каждого x спрашиваем: «видели ли мы уже target - x?»
        # Пара найдётся в момент, когда дойдём до второго её элемента.
        # Проверяем ДО вставки, поэтому элемент не спарится сам с собой.
        seen = {}
        for i, x in enumerate(nums):
            j = seen.get(target - x)
            if j is not None:
                return [j, i]
            seen[x] = i
        return []


ALL = {
    "BruteHalf": BruteHalf,
    "SortTwoPointers": SortTwoPointers,
    "HashTwoPass": HashTwoPass,
    "HashOnePass": HashOnePass,
}
