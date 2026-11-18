# 10. Regular Expression Matching
# https://leetcode.com/problems/regular-expression-matching/
#
# Дана строка s и шаблон p. Реализовать сопоставление с поддержкой:
#   '.' — любой один символ;
#   '*' — ноль или больше повторений ПРЕДЫДУЩЕГО элемента.
# Шаблон должен покрывать ВСЮ строку, а не её часть.
#
# Example 1: s = "aa", p = "a"   -> False  ("a" не покрывает всю "aa")
# Example 2: s = "aa", p = "a*"  -> True   ('*' повторяет 'a' дважды)
# Example 3: s = "ab", p = ".*"  -> True   (".*" — ноль или больше любых символов)
#
# Constraints:
#   1 <= s.length <= 20
#   1 <= p.length <= 20
#   s состоит только из строчных английских букв
#   p состоит только из строчных английских букв, '.' и '*'
#   Перед каждым '*' гарантированно стоит допустимый символ
from functools import cache


class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        @cache
        def dfs(i: int, j: int) -> bool:
            if j == len(p):
                return i == len(s)
            if j + 1 < len(p) and p[j + 1] == '*':
                return dfs(i, j + 2) or (i < len(s) and (s[i] == p[j] or p[j] == '.') and dfs(i + 1, j))
            if j < len(p) and p[j] == '.':
                return dfs(i + 1, j + 1)
            return i < len(s) and j < len(p) and s[i] == p[j] and dfs(i + 1, j + 1)
        return dfs(0, 0)


if __name__ == "__main__":
    sol = Solution()
    assert sol.isMatch("aa", "a") is False
    assert sol.isMatch("aa", "a*") is True
    assert sol.isMatch("ab", ".*") is True
    assert sol.isMatch("aab", "c*a*b") is True              # c* — ноль повторений
    assert sol.isMatch("mississippi", "mis*is*p*.") is False
    assert sol.isMatch("mississippi", "mis*is*ip*.") is True
    assert sol.isMatch("a", "ab*") is True                  # хвостовой x* может быть пустым
    assert sol.isMatch("a", ".*..a*") is False
    assert sol.isMatch("ab", ".*c") is False
    assert sol.isMatch("aaa", "a*a") is True                # '*' не должна съесть всё жадно
    assert sol.isMatch("aaa", "ab*a*c*a") is True
    assert sol.isMatch("abcd", "d*") is False
    assert sol.isMatch("a", "a.") is False                  # '.' — ровно один символ, не ноль
    assert sol.isMatch("bbbba", ".*a*a") is True
    assert sol.isMatch("aaaaaaaaaaaaaaaaaaab", "a*a*a*a*a*a*a*a*a*c") is False  # экспонента у наивного перебора
    print("OK")
