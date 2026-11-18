# 9. Palindrome Number
# https://leetcode.com/problems/palindrome-number/
#
# Дано целое x. Вернуть True, если x — палиндром (читается одинаково
# слева направо и справа налево), иначе False.
#
# Example 1: x = 121  -> True
# Example 2: x = -121 -> False   ("-121" справа налево — "121-")
# Example 3: x = 10   -> False   (справа налево — "01")
#
# Constraints:
#   -2^31 <= x <= 2^31 - 1
#
# Follow up: решить без перевода числа в строку.


class Solution:
    def isPalindrome(self, x: int) -> bool:
        return str(x) == str(x)[::-1]


if __name__ == "__main__":
    s = Solution()
    assert s.isPalindrome(121) is True
    assert s.isPalindrome(-121) is False
    assert s.isPalindrome(10) is False
    assert s.isPalindrome(0) is True
    assert s.isPalindrome(7) is True
    assert s.isPalindrome(11) is True
    assert s.isPalindrome(1221) is True
    assert s.isPalindrome(12321) is True
    assert s.isPalindrome(123) is False
    assert s.isPalindrome(100) is False            # нули в конце
    assert s.isPalindrome(1001) is True            # нули в середине
    assert s.isPalindrome(1000021) is False
    assert s.isPalindrome(-1) is False             # любое отрицательное — нет
    assert s.isPalindrome(2147483647) is False     # 2^31 - 1
    assert s.isPalindrome(-2147483648) is False    # -2^31
    assert s.isPalindrome(2147447412) is True      # палиндром у верхней границы
    print("OK")
