# 4. Median of Two Sorted Arrays
# https://leetcode.com/problems/median-of-two-sorted-arrays/
#
# Даны два массива nums1 (длины m) и nums2 (длины n), каждый отсортирован по неубыванию.
# Вернуть медиану объединения этих двух массивов.
# Требование: общая сложность O(log (m + n)).
#
# Медиана: если всего элементов нечётное число — средний элемент;
#          если чётное — среднее арифметическое двух средних.
#
# Example 1: nums1 = [1, 3],    nums2 = [2]    -> 2.0      (объединение [1, 2, 3])
# Example 2: nums1 = [1, 2],    nums2 = [3, 4] -> 2.5      (объединение [1, 2, 3, 4], (2 + 3) / 2)
#
# Constraints:
#   nums1.length == m, nums2.length == n
#   0 <= m <= 1000, 0 <= n <= 1000
#   1 <= m + n <= 2000
#   -10^6 <= nums1[i], nums2[i] <= 10^6


class Solution:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        # Ищем разрез по более короткому массиву.
        # Слева от разреза ровно half элементов, и каждый слева не больше каждого справа.
        if len(nums1) > len(nums2):
            nums1, nums2 = nums2, nums1
        m, n = len(nums1), len(nums2)
        half = (m + n + 1) // 2
        lo, hi = 0, m
        while lo <= hi:
            i = (lo + hi) // 2
            j = half - i
            left1 = nums1[i - 1] if i else float("-inf")
            right1 = nums1[i] if i < m else float("inf")
            left2 = nums2[j - 1] if j else float("-inf")
            right2 = nums2[j] if j < n else float("inf")
            if left1 <= right2 and left2 <= right1:
                if (m + n) % 2:
                    return float(max(left1, left2))
                return (max(left1, left2) + min(right1, right2)) / 2
            if left1 > right2:
                hi = i - 1
            else:
                lo = i + 1
        raise AssertionError("разрез не найден")


if __name__ == "__main__":
    s = Solution()
    assert s.findMedianSortedArrays([1, 3], [2]) == 2.0
    assert s.findMedianSortedArrays([1, 2], [3, 4]) == 2.5
    assert s.findMedianSortedArrays([], [1]) == 1.0
    assert s.findMedianSortedArrays([2], []) == 2.0
    assert s.findMedianSortedArrays([0, 0], [0, 0]) == 0.0
    assert s.findMedianSortedArrays([1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11]) == 6.0
    assert s.findMedianSortedArrays([1, 2, 3], [100, 200, 300]) == 51.5
    assert s.findMedianSortedArrays([1, 100], [2, 3]) == 2.5
    assert s.findMedianSortedArrays([-5, -3, -1], [-2]) == -2.5
    print("OK")
