# 7. Reverse Integer
# https://leetcode.com/problems/reverse-integer/
#
# Дано 32-битное знаковое целое x. Вернуть x с цифрами в обратном порядке.
# Если результат выходит за диапазон 32-битного знакового целого [-2^31, 2^31 - 1], вернуть 0.
#
# Считаем, что среда НЕ позволяет хранить 64-битные целые (знаковые и беззнаковые):
# промежуточные значения тоже должны помещаться в 32 бита.
#
# Example 1: x = 123  -> 321
# Example 2: x = -123 -> -321
# Example 3: x = 120  -> 21
#
# Constraints:
#   -2^31 <= x <= 2^31 - 1


class Solution:
    def reverse(self, x: int) -> int:
        reversed_x = int(str(abs(x))[::-1])
        if x > 0 and (x.bit_length() > 31 or reversed_x.bit_length() > 31):
            return 0
        if x < 0 and (x.bit_length() >= 32 or reversed_x.bit_length() >= 32):
            return 0
        return reversed_x * (-1 if x < 0 else 1)


if __name__ == "__main__":
    s = Solution()
    assert s.reverse(123) == 321
    assert s.reverse(-123) == -321
    assert s.reverse(120) == 21
    assert s.reverse(0) == 0
    assert s.reverse(1534236469) == 0          # 9646324351 > 2^31 - 1
    assert s.reverse(-2147483648) == 0         # минимум: разворот 8463847412 не влезает
    assert s.reverse(1463847412) == 2147483641 # влезает впритык
    assert s.reverse(-1463847412) == -2147483641
    assert s.reverse(-1563847412) == 0         # -2147483651 < -2^31
    assert s.reverse(2147483647) == 0         # 7463847412 не влезает
    print("OK")
