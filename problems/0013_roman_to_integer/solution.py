# 13. Roman to Integer
# https://leetcode.com/problems/roman-to-integer/
#
# Семь римских символов:
#   I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000
#
# Обычно символы идут от больших к меньшим, и значение — их сумма: XXVII = 10 + 10 + 5 + 1 + 1 = 27.
# Исключение — вычитание: меньший символ перед большим вычитается. Таких пар шесть:
#   IV = 4, IX = 9, XL = 40, XC = 90, CD = 400, CM = 900
#
# Дана римская запись s — вернуть число.
#
# Example 1: s = "III"     -> 3
# Example 2: s = "LVIII"   -> 58     (L = 50, V = 5, III = 3)
# Example 3: s = "MCMXCIV" -> 1994   (M = 1000, CM = 900, XC = 90, IV = 4)
#
# Constraints:
#   1 <= s.length <= 15
#   s состоит только из символов 'I', 'V', 'X', 'L', 'C', 'D', 'M'
#   Гарантируется, что s — корректная римская запись числа из диапазона [1, 3999]


class Solution:
    __ROMAN_TO_INT = {
        "I": 1,
        "IV": 4,
        "V": 5,
        "IX": 9,
        "X": 10,
        "XL": 40,
        "L": 50,
        "XC": 90,
        "C": 100,
        "CD": 400,
        "D": 500,
        "CM": 900,
        "M": 1000
    }

    def romanToInt(self, s: str) -> int:
        result: int = 0
        i: int = 0
        while i < len(s):
            if i + 1 < len(s) and s[i:i+2] in self.__ROMAN_TO_INT:
                result += self.__ROMAN_TO_INT[s[i:i+2]]
                i += 2
            else:
                result += self.__ROMAN_TO_INT[s[i]]
                i += 1
        return result


if __name__ == "__main__":
    s = Solution()
    assert s.romanToInt("III") == 3
    assert s.romanToInt("LVIII") == 58
    assert s.romanToInt("MCMXCIV") == 1994
    print("OK")
