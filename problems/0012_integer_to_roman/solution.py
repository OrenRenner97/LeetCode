# 12. Integer to Roman
# https://leetcode.com/problems/integer-to-roman/
#
# Семь римских символов:
#   I = 1, V = 5, X = 10, L = 50, C = 100, D = 500, M = 1000
#
# Число переводится в римскую запись по десятичным разрядам, от старшего к младшему:
#   - если разряд не начинается с 4 или 9 — берём символ с наибольшим значением,
#     не превосходящим остаток, дописываем его и вычитаем, затем повторяем;
#   - если разряд начинается с 4 или 9 — используется вычитательная форма:
#     4 = IV, 9 = IX, 40 = XL, 90 = XC, 400 = CD, 900 = CM (только эти шесть);
#   - подряд можно ставить не больше трёх одинаковых символов-степеней десяти (I, X, C, M);
#     V, L, D подряд не повторяются — для 4/9 нужна вычитательная форма.
#
# Example 1: num = 3749 -> "MMMDCCXLIX"
#   3000 = MMM, 700 = DCC, 40 = XL, 9 = IX
# Example 2: num = 58   -> "LVIII"
#   50 = L, 8 = VIII
# Example 3: num = 1994 -> "MCMXCIV"
#   1000 = M, 900 = CM, 90 = XC, 4 = IV
#
# Constraints:
#   1 <= num <= 3999


class Solution:
    def intToRoman(self, num: int) -> str:
        roman_digits = {
            1000: "M",
            900: "CM",
            500: "D",
            400: "CD",
            100: "C",
            90: "XC",
            50: "L",
            40: "XL",
            10: "X",
            9: "IX",
            5: "V",
            4: "IV",
            1: "I",
        }
        result = ""
        while num > 0:
            for value, symbol in roman_digits.items():
                if num >= value:
                    num -= value
                    result += symbol
                    break
        return result


if __name__ == "__main__":
    s = Solution()
    assert s.intToRoman(3749) == "MMMDCCXLIX"
    assert s.intToRoman(58) == "LVIII"
    assert s.intToRoman(1994) == "MCMXCIV"
    print("OK")
