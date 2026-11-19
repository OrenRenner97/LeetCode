"""11. Container With Most Water: альтернативные решения.

| # | Класс                  | Время      | Память | Идея                                                                    |
|---|------------------------|------------|--------|-------------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(n)       | O(1)   | два указателя с краёв, сдвигаем тот, что ниже                           |
| 1 | BruteForce             | O(n²)      | O(1)   | все пары — эталон и иллюстрация, почему нужен O(n)                      |
| 2 | TwoPointersInline      | O(n)       | O(1)   | то же, без вызовов max()/min() и с локальными переменными               |
| 3 | TwoPointersSkip        | O(n)       | O(1)   | после сдвига пропускаем все линии не выше текущей: площадь там не вырастет |
| 4 | SortByHeight           | O(n log n) | O(n)   | линии от высоких к низким; для каждой — самая дальняя из не более низких |
| 5 | NumpySortByHeight      | O(n log n) | O(n)   | то же векторно: argsort + minimum/maximum.accumulate                    |
"""
import numpy as np


class BruteForce:
    def maxArea(self, height: list[int]) -> int:
        n = len(height)
        best = 0
        for i in range(n):
            hi = height[i]
            for j in range(i + 1, n):
                area = (j - i) * (hi if hi < height[j] else height[j])
                if area > best:
                    best = area
        return best


class TwoPointersInline:
    def maxArea(self, height: list[int]) -> int:
        # Алгоритм тот же, что у Solution. Разница только в цене строки в CPython:
        # max(…, …) и min(…, …) — два вызова встроенных функций на шаг, if — нет.
        h = height
        left, right = 0, len(h) - 1
        best = 0
        while left < right:
            hl, hr = h[left], h[right]
            if hl < hr:
                area = (right - left) * hl
                left += 1
            else:
                area = (right - left) * hr
                right -= 1
            if area > best:
                best = area
        return best


class TwoPointersSkip:
    def maxArea(self, height: list[int]) -> int:
        # Сдвинули низкую стенку высоты m. Пока следующие линии не выше m, контейнер с ними
        # уже, а высота по-прежнему ≤ m: площадь не может вырасти. Пропускаем их без умножений.
        h = height
        left, right = 0, len(h) - 1
        best = 0
        while left < right:
            hl, hr = h[left], h[right]
            if hl < hr:
                area = (right - left) * hl
                if area > best:
                    best = area
                while left < right and h[left] <= hl:
                    left += 1
            else:
                area = (right - left) * hr
                if area > best:
                    best = area
                while left < right and h[right] <= hr:
                    right -= 1
        return best


class SortByHeight:
    def maxArea(self, height: list[int]) -> int:
        # Другой взгляд: у пары высота — min(h[i], h[j]). Идём по линиям от высоких к низким.
        # Когда обрабатываем линию i, все уже пройденные не ниже неё, значит, в паре с ними высота = h[i],
        # и выгоднее всего самая дальняя из них: минимальный или максимальный индекс среди пройденных.
        order = sorted(range(len(height)), key=height.__getitem__, reverse=True)
        lo = hi = order[0]
        best = 0
        for i in order[1:]:
            if i < lo:
                lo = i
            elif i > hi:
                hi = i
            # lo и hi уже учитывают i: тогда i - lo или hi - i равно 0 — это не мешает максимуму
            width = hi - i if hi - i > i - lo else i - lo
            area = width * height[i]
            if area > best:
                best = area
        return best


class NumpySortByHeight:
    def maxArea(self, height: list[int]) -> int:
        # SortByHeight без Python-цикла: после argsort по убыванию высоты накопленные min/max индексов —
        # это границы «уже пройденных» линий для каждой позиции. O(n log n), но всё в C.
        h = np.asarray(height, dtype=np.int64)
        order = np.argsort(-h, kind="stable")
        lo = np.minimum.accumulate(order)
        hi = np.maximum.accumulate(order)
        width = np.maximum(order - lo, hi - order)
        return int((width * h[order]).max())


ALL = {
    "BruteForce": BruteForce,
    "TwoPointersInline": TwoPointersInline,
    "TwoPointersSkip": TwoPointersSkip,
    "SortByHeight": SortByHeight,
    "NumpySortByHeight": NumpySortByHeight,
}
