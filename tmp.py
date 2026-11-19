# 11. Container With Most Water
# https://leetcode.com/problems/container-with-most-water/
#
# Дан массив height длины n: n вертикальных линий, i-я идёт от (i, 0) до (i, height[i]).
# Выбрать две линии, которые вместе с осью x образуют контейнер с наибольшим объёмом воды.
# Вернуть этот максимальный объём.
#
# Объём контейнера между линиями i < j: (j - i) * min(height[i], height[j]).
# Контейнер нельзя наклонять.
#
# Example 1: height = [1,8,6,2,5,4,8,3,7] -> 49   (линии 1 и 8: ширина 7, высота min(8, 7) = 7)
# Example 2: height = [1,1]               -> 1
#
# Constraints:
#   n == height.length
#   2 <= n <= 10^5
#   0 <= height[i] <= 10^4


class Solution:
    def maxArea(self, height: list[int]) -> int:
        left, right = 0, len(height) - 1
        max_area = 0
        while left < right:
            max_area = max(max_area, (right - left) * min(height[left], height[right]))
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        return max_area


if __name__ == "__main__":
    s = Solution()
    assert s.maxArea([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert s.maxArea([1, 1]) == 1
    assert s.maxArea([0, 0]) == 0
    assert s.maxArea([0, 5]) == 0                       # одна стенка нулевая — воды нет
    assert s.maxArea([4, 3, 2, 1, 4]) == 16             # крайние линии, хотя внутри ниже
    assert s.maxArea([1, 2, 1]) == 2
    assert s.maxArea([1, 2, 4, 3]) == 4
    assert s.maxArea([2, 3, 4, 5, 18, 17, 6]) == 17     # две высокие соседние: ширина 1
    assert s.maxArea([1, 3, 2, 5, 25, 24, 5]) == 24
    assert s.maxArea([5, 5, 5, 5, 5]) == 20
    assert s.maxArea(list(range(1, 11))) == 25          # возрастающая: 5 * 5
    assert s.maxArea(list(range(10, 0, -1))) == 25      # убывающая
    assert s.maxArea([10_000] * 100_000) == 10_000 * 99_999   # максимум по ограничениям: O(n²) не успеет
    print("OK")
