# 8. String to Integer (atoi)
# https://leetcode.com/problems/string-to-integer-atoi/
#
# Реализовать myAtoi(s): перевести строку в 32-битное знаковое целое.
# Алгоритм:
#   1. Пропустить ведущие пробелы (" ").
#   2. Знак: '-' или '+' (если есть; по умолчанию положительное).
#   3. Читать цифры, пока не встретится не-цифра или конец строки.
#      Ведущие нули пропускаются. Если цифр нет — результат 0.
#   4. Округление: если число вне [-2^31, 2^31 - 1], прижать к границе
#      (меньше -2^31 -> -2^31, больше 2^31 - 1 -> 2^31 - 1).
# Вернуть получившееся целое.
#
# Example 1: s = "42"            -> 42
# Example 2: s = " -042"         -> -42
# Example 3: s = "1337c0d3"      -> 1337
# Example 4: s = "0-1"           -> 0
# Example 5: s = "words and 987" -> 0
#
# Constraints:
#   0 <= s.length <= 200
#   s состоит из английских букв (строчных и заглавных), цифр (0-9), ' ', '+', '-' и '.'


class Solution:
    def myAtoi(self, s: str) -> int:
        result = 0
        sign = 0
        has_number = False
        for char in s:
            if char == ' ':
                if has_number or sign != 0:
                    break
                continue
            elif char == '+' or char == '-':
                if sign != 0:
                    break
                if has_number:
                    break
                sign = -1 if char == '-' else 1
            elif char.isdigit():
                if sign == 0:
                    sign = 1
                result = result * 10 + ord(char) - ord('0')
                has_number = True
            elif ord(char) in range(ord('a'), ord('z') + 1):
                if has_number:
                    break
                break
            elif char == '.':
                if has_number:
                    break
                break
            else:
                break
        result = result * sign
        if result < -2147483648:
            result = -2147483648
        elif result > 2147483647:
            result = 2147483647
        return result
                

if __name__ == "__main__":
    s = Solution()
    assert s.myAtoi("42") == 42
    assert s.myAtoi(" -042") == -42
    assert s.myAtoi("1337c0d3") == 1337
    assert s.myAtoi("0-1") == 0
    assert s.myAtoi("words and 987") == 0
    assert s.myAtoi("") == 0
    assert s.myAtoi("   ") == 0
    assert s.myAtoi("+") == 0
    assert s.myAtoi("+-12") == 0               # два знака подряд — цифр нет
    assert s.myAtoi("-+12") == 0
    assert s.myAtoi("  +0 123") == 0           # пробел обрывает число
    assert s.myAtoi("3.14159") == 3
    assert s.myAtoi(".1") == 0
    assert s.myAtoi("00000-42a1234") == 0
    assert s.myAtoi("\t42") == 0               # пропускаем только ' ', не любые пробельные
    assert s.myAtoi("2147483647") == 2147483647
    assert s.myAtoi("2147483648") == 2147483647    # прижали к максимуму
    assert s.myAtoi("-2147483648") == -2147483648
    assert s.myAtoi("-2147483649") == -2147483648  # прижали к минимуму
    assert s.myAtoi("-91283472332") == -2147483648
    assert s.myAtoi("00000000000000000000000000001") == 1  # длинные ведущие нули
    assert s.myAtoi("1" + "0" * 100) == 2147483647         # очень длинное число
    assert s.myAtoi("  +  413") == 0
    print("OK")
