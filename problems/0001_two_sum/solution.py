# 1. Two Sum — https://leetcode.com/problems/two-sum/
#
# Дан массив nums и число target. Вернуть индексы двух чисел, сумма которых равна target.
# Ровно одно решение, один элемент дважды использовать нельзя, порядок ответа любой.
#
# Example 1: nums = [2,7,11,15], target = 9  -> [0,1]
# Example 2: nums = [3,2,4],     target = 6  -> [1,2]
# Example 3: nums = [3,3],       target = 6  -> [0,1]
#
# Constraints: 2 <= len(nums) <= 10^4, -10^9 <= nums[i], target <= 10^9
# Follow-up: можно ли быстрее, чем O(n^2)?
from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for index1, item1 in enumerate(nums):
            for index2, item2 in enumerate(nums):
                if index1 != index2 and item1 + item2 == target:
                    return [index1, index2]


if __name__ == "__main__":
    s = Solution()
    assert sorted(s.twoSum([2, 7, 11, 15], 9)) == [0, 1]
    assert sorted(s.twoSum([3, 2, 4], 6)) == [1, 2]
    assert sorted(s.twoSum([3, 3], 6)) == [0, 1]
    print("OK")
