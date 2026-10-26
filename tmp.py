# 3. Longest Substring Without Repeating Characters
# https://leetcode.com/problems/longest-substring-without-repeating-characters/
#
# Дана строка s. Найти длину самой длинной ПОДСТРОКИ (непрерывного куска) без повторяющихся символов.
#
# Example 1: s = "abcabcbb" -> 3   ("abc")
# Example 2: s = "bbbbb"    -> 1   ("b")
# Example 3: s = "pwwkew"   -> 3   ("wke"; "pwke" не подходит: это подпоследовательность, а не подстрока)
#
# Constraints: 0 <= len(s) <= 5 * 10^4; s состоит из английских букв, цифр, символов и пробелов.


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        if len(s) < 2:
            return len(s)
        current_index = 1
        left_index = 0
        max_length = 1
        while current_index < len(s):
            substring = s[left_index:current_index+1]
            if len(substring) == len(set(substring)):
                max_length = max(max_length, len(substring))
            else:
                left_index += 1
            current_index += 1
        return max_length


if __name__ == "__main__":
    s = Solution()
    assert s.lengthOfLongestSubstring("abcabcbb") == 3
    assert s.lengthOfLongestSubstring("bbbbb") == 1
    assert s.lengthOfLongestSubstring("pwwkew") == 3
    assert s.lengthOfLongestSubstring("") == 0
    assert s.lengthOfLongestSubstring("mq") == 2
    print("OK")
