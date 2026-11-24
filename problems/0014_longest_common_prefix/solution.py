# 14. Longest Common Prefix
# https://leetcode.com/problems/longest-common-prefix/
#
# Дан массив строк strs. Найти самый длинный общий префикс всех строк.
# Если общего префикса нет — вернуть пустую строку "".
#
# Example 1: strs = ["flower", "flow", "flight"] -> "fl"
# Example 2: strs = ["dog", "racecar", "car"]    -> ""   (общего префикса нет)
#
# Constraints:
#   1 <= strs.length <= 200
#   0 <= strs[i].length <= 200
#   strs[i] состоит только из строчных английских букв (может быть пустой)


class Solution:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        result_common_prefix = strs[0]
        for word in strs:
            common_length = min(len(result_common_prefix), len(word))
            result_common_prefix = result_common_prefix[:common_length]
            for i in range(min(len(result_common_prefix), len(word))):
                if word[i] != result_common_prefix[i]:
                    result_common_prefix = result_common_prefix[:i]
                    break
        return result_common_prefix


if __name__ == "__main__":
    s = Solution()
    assert s.longestCommonPrefix(["flower", "flow", "flight"]) == "fl"
    assert s.longestCommonPrefix(["dog", "racecar", "car"]) == ""
    assert s.longestCommonPrefix(["ab", "a"]) == "a"
    print("OK")
