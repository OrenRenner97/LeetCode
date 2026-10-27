"""4. Median of Two Sorted Arrays: альтернативные решения.

m, n = длины массивов, N = m + n, R = диапазон значений (по условию 2·10^6 + 1).

| # | Класс                   | Время               | Память | Идея                                                     |
|---|-------------------------|---------------------|--------|----------------------------------------------------------|
| 0 | Solution (solution.py)  | O(log min(m, n))    | O(1)   | бинпоиск по разрезу короткого массива                    |
| 1 | SortConcat              | O(N log N) / O(N)*  | O(N)   | sorted(nums1 + nums2) и взять середину                   |
| 2 | MergeFull               | O(N)                | O(N)   | слияние двумя указателями в новый список                 |
| 3 | MergeHalf               | O(N)                | O(1)   | идём указателями до середины, ничего не храним           |
| 4 | HeapqMerge              | O(N)                | O(1)   | ленивое heapq.merge + islice до середины                 |
| 5 | KthElement              | O(log N)            | O(1)   | k-й элемент: каждый шаг отбрасывает k/2 элементов        |
| 6 | ValueBinarySearch       | O(log R · log N)    | O(1)   | бинпоиск по ЗНАЧЕНИЮ: сколько элементов <= x (bisect)    |

* Timsort находит в nums1 + nums2 две готовые отсортированные серии и просто сливает их: на деле O(N).
"""
from bisect import bisect_right
from heapq import merge
from itertools import islice


def _median_of_sorted(arr: list[int]) -> float:
    n = len(arr)
    if n % 2:
        return float(arr[n // 2])
    return (arr[n // 2 - 1] + arr[n // 2]) / 2


class SortConcat:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Самое короткое решение. Игнорирует то, что массивы уже отсортированы,
        # но Timsort это всё равно заметит (две серии → одно слияние).
        return _median_of_sorted(sorted(nums1 + nums2))


class MergeFull:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Классическое слияние из merge sort: берём меньший из двух голов.
        merged = []
        i = j = 0
        while i < len(nums1) and j < len(nums2):
            if nums1[i] <= nums2[j]:
                merged.append(nums1[i])
                i += 1
            else:
                merged.append(nums2[j])
                j += 1
        merged.extend(nums1[i:])
        merged.extend(nums2[j:])
        return _median_of_sorted(merged)


class MergeHalf:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # То же слияние, но останавливаемся на середине и помним только два последних
        # взятых элемента: prev и cur. Вторая половина массивов не нужна.
        m, n = len(nums1), len(nums2)
        total = m + n
        i = j = 0
        prev = cur = 0
        for _ in range(total // 2 + 1):
            prev = cur
            if j >= n or (i < m and nums1[i] <= nums2[j]):
                cur = nums1[i]
                i += 1
            else:
                cur = nums2[j]
                j += 1
        if total % 2:
            return float(cur)
        return (prev + cur) / 2


class HeapqMerge:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # heapq.merge — ленивое слияние отсортированных итераторов (написано на C).
        # islice берёт только первые total//2 + 1 элементов, остальное не трогаем.
        total = len(nums1) + len(nums2)
        head = list(islice(merge(nums1, nums2), total // 2 + 1))
        if total % 2:
            return float(head[-1])
        return (head[-2] + head[-1]) / 2


class KthElement:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Медиана = k-й по величине элемент (или среднее двух соседних).
        # Ищем k-й: сравниваем по k/2-му элементу в каждом массиве. У кого он меньше,
        # те k/2 элементов точно стоят до k-го: отбрасываем их, k уменьшается.
        # k каждый раз уменьшается вдвое → O(log N). Срезов нет, только сдвиг индексов.
        def kth(k: int) -> int:  # k с единицы
            i = j = 0
            while True:
                if i == len(nums1):
                    return nums2[j + k - 1]
                if j == len(nums2):
                    return nums1[i + k - 1]
                if k == 1:
                    return min(nums1[i], nums2[j])
                ni = min(i + k // 2, len(nums1))
                nj = min(j + k // 2, len(nums2))
                if nums1[ni - 1] <= nums2[nj - 1]:
                    k -= ni - i
                    i = ni
                else:
                    k -= nj - j
                    j = nj

        total = len(nums1) + len(nums2)
        if total % 2:
            return float(kth(total // 2 + 1))
        return (kth(total // 2) + kth(total // 2 + 1)) / 2


class ValueBinarySearch:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Бинпоиск не по индексам, а по значениям: k-й элемент — это наименьшее x,
        # для которого «элементов <= x» не меньше k. Счёт — два bisect, O(log N).
        # Работает только для целых (по условию так и есть): нужен шаг «x + 1».
        def kth(k: int) -> int:
            lo = min(a[0] for a in (nums1, nums2) if a)
            hi = max(a[-1] for a in (nums1, nums2) if a)
            while lo < hi:
                mid = (lo + hi) // 2
                if bisect_right(nums1, mid) + bisect_right(nums2, mid) >= k:
                    hi = mid
                else:
                    lo = mid + 1
            return lo

        total = len(nums1) + len(nums2)
        if total % 2:
            return float(kth(total // 2 + 1))
        return (kth(total // 2) + kth(total // 2 + 1)) / 2


ALL = {
    "SortConcat": SortConcat,
    "MergeFull": MergeFull,
    "MergeHalf": MergeHalf,
    "HeapqMerge": HeapqMerge,
    "KthElement": KthElement,
    "ValueBinarySearch": ValueBinarySearch,
}
