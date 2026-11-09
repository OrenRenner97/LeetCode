# 5. Longest Palindromic Substring
# https://leetcode.com/problems/longest-palindromic-substring/
#
# Дана строка s. Вернуть самую длинную ПОДСТРОКУ (непрерывный кусок), которая является палиндромом
# (читается одинаково слева направо и справа налево).
# Если самых длинных несколько — можно вернуть любую.
#
# Example 1: s = "babad" -> "bab"   ("aba" тоже правильный ответ)
# Example 2: s = "cbbd"  -> "bb"
#
# Constraints:
#   1 <= s.length <= 1000
#   s состоит только из цифр и английских букв.


class Solution:
    def longestPalindrome(self, s: str) -> str:
        max_length = 0
        max_length_substring = ""
        for i in range(len(s)):
            for j in range(i, len(s)):
                if s[i:j+1] == s[i:j+1][::-1]:
                    if j - i + 1 > max_length:
                        max_length = j - i + 1
                        max_length_substring = s[i:j+1]
        return max_length_substring

if __name__ == "__main__":
    s = Solution()
    assert s.longestPalindrome("babad") in ("bab", "aba")
    assert s.longestPalindrome("cbbd") == "bb"
    assert s.longestPalindrome("a") == "a"
    assert s.longestPalindrome("ac") in ("a", "c")
    assert s.longestPalindrome("racecar") == "racecar"
    assert s.longestPalindrome("forgeeksskeegfor") == "geeksskeeg"
    assert s.longestPalindrome("aaaa") == "aaaa"
    print("OK")
