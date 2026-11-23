"""13. Roman to Integer: альтернативные решения.

k = len(s) ≤ 15.

| # | Класс                  | Время | Память  | Идея                                                                       |
|---|------------------------|-------|---------|----------------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(k)  | O(1)    | таблица из 13 «токенов»: сначала пробуем пару символов, потом один          |
| 1 | SubtractNext           | O(k)  | O(1)    | символ меньше следующего — вычитается (классика)                           |
| 2 | ReverseScan            | O(k)  | O(1)    | справа налево: символ меньше предыдущего (правого) — вычитается            |
| 3 | PairCount              | O(k)  | O(1)    | сумма всех символов на C, затем поправка за 6 вычитательных пар (`str.count`) |
| 4 | ReplacePairs           | O(k)  | O(k)    | 6 replace: IV → IIII, … — дальше просто сумма символов                     |
| 5 | DigitRegex             | O(k)  | O(1)    | регулярка по разрядам M{0,3}(…)(…)(…), каждая группа → таблица             |
| 6 | FullLookup             | O(k)  | O(4000) | словарь всех 3999 записей → число: один хэш строки                         |
"""
import re

_V = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


class SubtractNext:
    def romanToInt(self, s: str) -> int:
        # Вычитательная форма — ровно случай «меньший символ перед большим». Сравниваем соседей.
        v = _V
        total = 0
        prev = 0
        for c in s:
            cur = v[c]
            if prev < cur:
                total -= 2 * prev     # prev уже прибавили — убираем дважды
            total += cur
            prev = cur
        return total


class ReverseScan:
    def romanToInt(self, s: str) -> int:
        # Справа налево решение о символе принимается сразу: он меньше правого соседа — вычитается.
        v = _V
        total = 0
        right = 0
        for c in reversed(s):
            cur = v[c]
            if cur < right:
                total -= cur
            else:
                total += cur
            right = cur
        return total


_CORRECTIONS = (("IV", 2), ("IX", 2), ("XL", 20), ("XC", 20), ("CD", 200), ("CM", 200))


class PairCount:
    def romanToInt(self, s: str) -> int:
        # Наивная сумма считает IV как 1 + 5 = 6 вместо 4: перебор на 2 · (меньший символ).
        # sum(map(...)) и str.count идут на C — в Python-цикле нет ни одного шага по символам.
        total = sum(map(_V.__getitem__, s))
        for pair, extra in _CORRECTIONS:
            if pair in s:
                total -= extra * s.count(pair)
        return total


_EXPAND = (("CM", "DCCCC"), ("CD", "CCCC"), ("XC", "LXXXX"), ("XL", "XXXX"), ("IX", "VIIII"), ("IV", "IIII"))


class ReplacePairs:
    def romanToInt(self, s: str) -> int:
        # Обратная сторона UnaryReplace из задачи 12: раскрываем вычитательные формы в «сложительные».
        for short, long in _EXPAND:
            s = s.replace(short, long)
        return sum(map(_V.__getitem__, s))


_DIGIT_FORMS = (
    ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"),
    ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"),
    ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"),
)
_ONES, _TENS, _HUNDREDS = ({form: d * mul for d, form in enumerate(forms)}
                           for forms, mul in zip(_DIGIT_FORMS, (1, 10, 100)))
_ROMAN_RE = re.compile(r"(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")


class DigitRegex:
    def romanToInt(self, s: str) -> int:
        # Разбор по разрядам — обратный DigitTables. Заодно проверка: неканоническое (IIII, IC) не совпадёт.
        m, c, x, i = _ROMAN_RE.fullmatch(s).groups()
        return 1000 * len(m) + _HUNDREDS[c] + _TENS[x] + _ONES[i]


def _to_roman(n: int) -> str:
    return "M" * (n // 1000) + _DIGIT_FORMS[2][n // 100 % 10] + _DIGIT_FORMS[1][n // 10 % 10] + _DIGIT_FORMS[0][n % 10]


_TABLE = {_to_roman(n): n for n in range(1, 4000)}


class FullLookup:
    def romanToInt(self, s: str) -> int:
        # Корректных записей всего 3999 — словарь целиком (~400 КБ), строится один раз.
        # O(k) — это хэш строки (а у литералов и интернированных строк он ещё и закэширован).
        return _TABLE[s]


ALL = {
    "SubtractNext": SubtractNext,
    "ReverseScan": ReverseScan,
    "PairCount": PairCount,
    "ReplacePairs": ReplacePairs,
    "DigitRegex": DigitRegex,
    "FullLookup": FullLookup,
}
