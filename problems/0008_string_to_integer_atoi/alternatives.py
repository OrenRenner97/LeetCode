"""8. String to Integer (atoi): альтернативные решения.

n = len(s) ≤ 200. Все решения O(n): разница в читаемости, в том, растёт ли промежуточное
число за пределы int32, и в цене одного вызова в CPython.

| # | Класс                  | 32 бита? | Идея                                                                   |
|---|------------------------|----------|------------------------------------------------------------------------|
| 0 | Solution (solution.py) | нет      | один цикл, фаза восстанавливается по флагам sign / has_number          |
| 1 | Phases                 | нет      | три фазы подряд по индексу: пробелы → знак → цифры, прижатие в конце   |
| 2 | PhasesGuard            | да       | то же, но копим в отрицательных и останавливаемся у границы, как в C   |
| 3 | Regex                  | нет      | одно регулярное выражение ` *([+-]?[0-9]+)` + int + прижатие          |
| 4 | StripPrefix            | да*      | фазы встроенными str-методами: lstrip(' '), lstrip(цифры) даёт длину   |
| 5 | Automaton              | нет      | конечный автомат: таблица переходов «состояние × класс символа»        |

* int() вызывается только от строки ≤ 10 цифр; длиннее — ответ уже известен (граница).
Цифры везде — только '0'…'9': str.isdigit() и \\d в re пропускают Unicode-цифры ('²', '٣').
"""
import re

INT_MAX = 2**31 - 1   # 2147483647
INT_MIN = -2**31      # −2147483648
_DIGITS = "0123456789"


def _clamp(x: int) -> int:
    return max(INT_MIN, min(INT_MAX, x))


class Phases:
    def myAtoi(self, s: str) -> int:
        # Алгоритм — это три фазы подряд, и код повторяет их по порядку.
        # Индекс i сам помнит, где мы, поэтому флаги не нужны.
        n, i = len(s), 0
        while i < n and s[i] == " ":
            i += 1
        sign = 1
        if i < n and s[i] in "+-":
            sign = -1 if s[i] == "-" else 1
            i += 1
        result = 0
        while i < n and "0" <= s[i] <= "9":
            result = result * 10 + (ord(s[i]) - 48)
            i += 1
        return _clamp(sign * result)


_MIN_DIV, _MIN_LAST = -214748364, -8   # INT_MIN = _MIN_DIV·10 + _MIN_LAST (деление как в C)


class PhasesGuard:
    def myAtoi(self, s: str) -> int:
        # Строгий 32-битный вариант: ни одно значение не выходит за [−2³¹, 2³¹ − 1].
        # Копим со знаком минус (−2³¹ есть, +2³¹ нет — та же идея, что в задаче 7)
        # и проверяем ДО шага rev·10 − d. Как только не влезает — ответ известен, дальше не читаем.
        n, i = len(s), 0
        while i < n and s[i] == " ":
            i += 1
        neg = False
        if i < n and s[i] in "+-":
            neg = s[i] == "-"
            i += 1
        rev = 0                                   # rev ≤ 0 всё время
        while i < n and "0" <= s[i] <= "9":
            d = -(ord(s[i]) - 48)                 # цифра со знаком минус: 0…−9
            if rev < _MIN_DIV or (rev == _MIN_DIV and d < _MIN_LAST):
                return INT_MIN if neg else INT_MAX
            rev = rev * 10 + d
            i += 1
        if neg:
            return rev
        return INT_MAX if rev < -INT_MAX else -rev   # −2³¹ нельзя сделать положительным


_ATOI_RE = re.compile(r" *([+-]?[0-9]+)")   # не \d: он матчит Unicode-цифры


class Regex:
    def myAtoi(self, s: str) -> int:
        # Вся грамматика в одной строке. match якорится в начале строки, сам ищет до первой не-цифры.
        # int() понимает знак и ведущие нули. Минус: строит большое число (до 200 цифр).
        m = _ATOI_RE.match(s)
        return _clamp(int(m.group(1))) if m else 0


class StripPrefix:
    def myAtoi(self, s: str) -> int:
        # Те же фазы, но каждая — один вызов C-метода строки вместо цикла байткода.
        # Трюк: len(t) − len(t.lstrip(цифры)) — длина префикса из цифр.
        t = s.lstrip(" ")
        neg = t[:1] == "-"
        if t[:1] in ("+", "-"):
            t = t[1:]
        k = len(t) - len(t.lstrip(_DIGITS))
        digits = t[:k].lstrip("0")
        if len(digits) > 10:                      # ≥ 10¹⁰ > 2³¹ — большой int не строим
            return INT_MIN if neg else INT_MAX
        r = int(digits) if digits else 0
        return _clamp(-r if neg else r)


# Состояния автомата и классы символов.
_START, _SIGNED, _NUMBER, _END = range(4)
_SPACE, _SIGN, _DIGIT, _OTHER = range(4)
_NEXT = (
    #  пробел   знак     цифра    другое
    (_START, _SIGNED, _NUMBER, _END),   # _START: пропускаем пробелы
    (_END,   _END,    _NUMBER, _END),   # _SIGNED: после знака — только цифра
    (_END,   _END,    _NUMBER, _END),   # _NUMBER: цифры, пока идут
)


def _char_class(c: str) -> int:
    if c == " ":
        return _SPACE
    if c == "+" or c == "-":
        return _SIGN
    if "0" <= c <= "9":
        return _DIGIT
    return _OTHER


class Automaton:
    def myAtoi(self, s: str) -> int:
        # Официальный разбор LeetCode: правила не в if-ах, а в таблице переходов.
        # Это обобщение решения из solution.py: там состояние было закодировано парой флагов.
        # Плюс — грамматику легко расширить (например, разрешить '_' между цифрами), меняя таблицу.
        state, sign, result = _START, 1, 0
        for c in s:
            state = _NEXT[state][_char_class(c)]
            if state == _END:
                break
            if state == _SIGNED:
                sign = -1 if c == "-" else 1
            elif state == _NUMBER:
                result = result * 10 + (ord(c) - 48)
        return _clamp(sign * result)


ALL = {
    "Phases": Phases,
    "PhasesGuard": PhasesGuard,
    "Regex": Regex,
    "StripPrefix": StripPrefix,
    "Automaton": Automaton,
}
