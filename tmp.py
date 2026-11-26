# 15. 3Sum
# https://leetcode.com/problems/3sum/
#
# Дан массив целых чисел nums. Вернуть все тройки [nums[i], nums[j], nums[k]],
# такие что i != j, i != k, j != k и nums[i] + nums[j] + nums[k] == 0.
# В ответе не должно быть одинаковых троек (порядок троек и чисел внутри не важен).
#
# Example 1: nums = [-1, 0, 1, 2, -1, -4] -> [[-1, -1, 2], [-1, 0, 1]]
# Example 2: nums = [0, 1, 1]             -> []
# Example 3: nums = [0, 0, 0]             -> [[0, 0, 0]]
#
# Constraints:
#   3 <= nums.length <= 3000
#   -10^5 <= nums[i] <= 10^5


class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        result = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                for k in range(j + 1, len(nums)):
                    if nums[i] + nums[j] + nums[k] == 0:
                        result.add(tuple(sorted([nums[i], nums[j], nums[k]])))
        return list(result)


def _norm(triplets: list[list[int]]) -> list[tuple[int, ...]]:
    return sorted(tuple(sorted(t)) for t in triplets)


if __name__ == "__main__":
    s = Solution()
    assert _norm(s.threeSum([-1, 0, 1, 2, -1, -4])) == [(-1, -1, 2), (-1, 0, 1)]
    assert _norm(s.threeSum([0, 1, 1])) == []
    assert _norm(s.threeSum([0, 0, 0])) == [(0, 0, 0)]
    assert _norm(s.threeSum([0, 0, 0, 0])) == [(0, 0, 0)]
    assert _norm(s.threeSum([-2, 0, 1, 1, 2])) == [(-2, 0, 2), (-2, 1, 1)]
    print("OK")
