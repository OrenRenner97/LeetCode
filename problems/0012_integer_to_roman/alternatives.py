"""12. Integer to Roman: альтернативные решения.

k — число символов в ответе (≤ 15, максимум у 3888 = MMMDCCCLXXXVIII), 13 — размер таблицы номиналов.

| # | Класс                  | Время      | Память  | Идея                                                                     |
|---|------------------------|------------|---------|--------------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(k · 13)  | O(1)    | жадно: после каждого символа поиск номинала с начала таблицы             |
| 1 | GreedyDivmod           | O(13)      | O(1)    | один проход по таблице: divmod даёт сразу число повторов символа         |
| 2 | GreedyWhile            | O(13 + k)  | O(1)    | один проход, `while num >= value` вместо возврата в начало              |
| 3 | DigitTables            | O(1)       | O(1)    | четыре таблицы по разрядам: тысячи + сотни + десятки + единицы           |
| 4 | DigitPattern           | O(1)       | O(1)    | одна таблица шаблонов цифры 0–9 ("", "1", …, "19"), символы подставляются по разряду |
| 5 | FullLookup             | O(1)       | O(4000) | все 3999 ответов заранее — один индекс в списке                         |
| 6 | UnaryReplace           | O(num)     | O(num)  | "I" × num, затем замены IIIII→V, VV→X, … и вычитательные формы           |
"""

_PAIRS = (
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)


class GreedyDivmod:
    def intToRoman(self, num: int) -> str:
        # Номинал повторяется подряд, только пока остаток ≥ его значения, — сколько раз, говорит divmod.
        # Возвращаться в начало таблицы не нужно: старшие номиналы остаток уже не вместит.
        parts = []
        for value, symbol in _PAIRS:
            if num >= value:
                count, num = divmod(num, value)
                parts.append(symbol * count)
        return "".join(parts)


class GreedyWhile:
    def intToRoman(self, num: int) -> str:
        # Тот же один проход, но без divmod: повторяем символ, пока номинал помещается (≤ 3 раза).
        result = ""
        for value, symbol in _PAIRS:
            while num >= value:
                num -= value
                result += symbol
        return result


_THOUSANDS = ("", "M", "MM", "MMM")
_HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
_TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
_ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")


class DigitTables:
    def intToRoman(self, num: int) -> str:
        # Римская запись — конкатенация записей разрядов, каждый разряд независим.
        return _THOUSANDS[num // 1000] + _HUNDREDS[num // 100 % 10] + _TENS[num // 10 % 10] + _ONES[num % 10]


# Шаблон цифры в терминах (единица, пятёрка, десятка) разряда: 1 → один, 5 → пять, X → десять.
_PATTERNS = ("", "1", "11", "111", "15", "5", "51", "511", "5111", "1X")
_SYMBOLS = ("IVX", "XLC", "CDM", "M")   # (one, five, ten) для единиц, десятков, сотен, тысяч


class DigitPattern:
    def intToRoman(self, num: int) -> str:
        # Все разряды устроены одинаково, отличаются только символы: одна таблица вместо четырёх.
        # Тысячи: цифра ≤ 3, шаблон состоит из одних "1" — пятёрка и десятка не нужны.
        digits = str(num)
        n = len(digits)
        parts = []
        for pos, d in enumerate(digits):
            pattern = _PATTERNS[ord(d) - 48]
            if pattern:
                parts.append(pattern.translate(_TRANS[n - 1 - pos]))
        return "".join(parts)


_TRANS = [str.maketrans({"1": s[0], "5": s[1:2] or None, "X": s[2:3] or None}) for s in _SYMBOLS]


_TABLE = [""] + [DigitTables().intToRoman(i) for i in range(1, 4000)]


class FullLookup:
    def intToRoman(self, num: int) -> str:
        # Вход ограничен 1..3999: проще всё посчитать заранее (≈ 4000 строк, ~250 КБ) и брать по индексу.
        return _TABLE[num]


class UnaryReplace:
    def intToRoman(self, num: int) -> str:
        # Римские цифры как сжатие унарной записи: группы из пяти/двух одинаковых символов сворачиваются
        # в следующий номинал, затем «4 одинаковых» и «пятёрка + 4» заменяются вычитательными формами.
        # Порядок замен важен: DCCCC → CM надо сделать раньше, чем CCCC → CD.
        s = "I" * num
        for small, big in (("IIIII", "V"), ("VV", "X"), ("XXXXX", "L"), ("LL", "C"),
                           ("CCCCC", "D"), ("DD", "M")):
            s = s.replace(small, big)
        for long, short in (("DCCCC", "CM"), ("CCCC", "CD"), ("LXXXX", "XC"), ("XXXX", "XL"),
                            ("VIIII", "IX"), ("IIII", "IV")):
            s = s.replace(long, short)
        return s


ALL = {
    "GreedyDivmod": GreedyDivmod,
    "GreedyWhile": GreedyWhile,
    "DigitTables": DigitTables,
    "DigitPattern": DigitPattern,
    "FullLookup": FullLookup,
    "UnaryReplace": UnaryReplace,
}
