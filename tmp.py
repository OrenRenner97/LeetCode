# 6. Zigzag Conversion
# https://leetcode.com/problems/zigzag-conversion/
#
# Строку s пишут «зигзагом» в numRows строк: сверху вниз по первому столбцу, потом по диагонали
# вверх вправо до первой строки, снова вниз и т.д. Затем читают построчно, слева направо.
# Вернуть получившуюся строку.
#
# Пример для s = "PAYPALISHIRING", numRows = 3:
#
#   P   A   H   N
#   A P L S I I G
#   Y   I   R
#
# Построчно: "PAHN" + "APLSIIG" + "YIR" = "PAHNAPLSIIGYIR"
#
# Example 1: s = "PAYPALISHIRING", numRows = 3 -> "PAHNAPLSIIGYIR"
# Example 2: s = "PAYPALISHIRING", numRows = 4 -> "PINALSIGYAHRPI"
#
#   P     I    N
#   A   L S  I G
#   Y A   H R
#   P     I
#
# Example 3: s = "A", numRows = 1 -> "A"
#
# Constraints:
#   1 <= s.length <= 1000
#   s состоит из английских букв (строчных и заглавных), ',' и '.'
#   1 <= numRows <= 1000


class Solution:
    def convert(self, s: str, numRows: int) -> str:
        dict_with_rows = {i: "" for i in range(numRows)}
        action_sign = 1
        current_row = 0
        for index, char in enumerate(s):
            if current_row in dict_with_rows:
                dict_with_rows[current_row] += char
            else:
                dict_with_rows[current_row] = char
            if current_row == 0:
                action_sign = 1
            elif current_row == numRows - 1:
                action_sign = -1
            current_row += action_sign
        return "".join(dict_with_rows.values())


if __name__ == "__main__":
    s = Solution()
    assert s.convert("PAYPALISHIRING", 3) == "PAHNAPLSIIGYIR"
    assert s.convert("PAYPALISHIRING", 4) == "PINALSIGYAHRPI"
    assert s.convert("A", 1) == "A"
    assert s.convert("AB", 1) == "AB"             # одна строка: зигзага нет
    assert s.convert("AB", 5) == "AB"             # строк больше, чем символов
    assert s.convert("ABCD", 2) == "ACBD"         # две строки: чётные и нечётные позиции
    assert s.convert("ABCDE", 4) == "ABCED"       # E уже на диагонали вверх
    print("OK")
