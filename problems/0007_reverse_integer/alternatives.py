"""7. Reverse Integer: альтернативные решения.

d = число цифр (≤ 10). Все решения O(d) по времени: разница не в асимптотике, а в том,
выполнено ли условие «нельзя хранить 64-битные числа» и сколько стоит один вызов в CPython.

| # | Класс                  | 32 бита? | Идея                                                                  |
|---|------------------------|----------|-----------------------------------------------------------------------|
| 0 | Solution (solution.py) | нет      | разворот строки, int, проверка через bit_length                       |
| 1 | StrCompare             | нет      | то же, но знак сразу и одно сравнение с [−2³¹, 2³¹ − 1]               |
| 2 | StrLexCompare          | да*      | ни одного большого int: 10-значный разворот сравниваем как строку     |
| 3 | PopPushGuard           | да       | цифры через divmod, переполнение ловим ДО rev·10 + d                  |
| 4 | NegativeAccumulate     | да       | как в C: копим в отрицательных, abs(−2³¹) не существует в int32        |
| 5 | Wraparound32           | да       | как в Java: считаем с обёрткой по модулю 2³², ловим переполнение после |

* int() вызывается только от строки, которая заведомо помещается в int32.
"""

INT_MAX = 2**31 - 1   # 2147483647
INT_MIN = -2**31      # −2147483648
_MAX_STR = str(INT_MAX)


class StrCompare:
    def reverse(self, x: int) -> int:
        # Самый «питоновский»: int неограничен, поэтому сначала считаем, потом проверяем.
        # Нарушает условие: промежуточное значение доходит до 9 646 324 351 (34 бита).
        r = int(str(abs(x))[::-1])
        if x < 0:
            r = -r
        return r if INT_MIN <= r <= INT_MAX else 0


class StrLexCompare:
    def reverse(self, x: int) -> int:
        # Переполнение возможно только у 10-значного разворота. Строки одинаковой длины
        # из цифр сравниваются лексикографически так же, как числа — int не нужен.
        # Для отрицательных граница 2147483648, но разворот 10-значного x с ней совпасть не может
        # (тогда x = −8463847412, вне диапазона), поэтому хватает той же границы, что у положительных.
        digits = str(abs(x))[::-1]
        if len(digits) == 10 and digits > _MAX_STR:
            return 0
        r = int(digits)
        return -r if x < 0 else r


class PopPushGuard:
    def reverse(self, x: int) -> int:
        # Классика: rev = rev·10 + d. Перед шагом проверяем, что результат влезет:
        # rev > INT_MAX // 10 — точно нет; rev == INT_MAX // 10 — только если d ≤ 7.
        # Работаем с модулем: у Python // и % округляют к −∞, на отрицательных цифры были бы «не те».
        # abs(INT_MIN) = 2³¹ сам не влезает в int32 — в C так нельзя, см. NegativeAccumulate.
        sign = -1 if x < 0 else 1
        x = abs(x)
        limit = INT_MAX if sign > 0 else -INT_MIN   # 2147483647 / 2147483648
        last = limit % 10                            # 7 / 8
        rev = 0
        while x:
            x, d = divmod(x, 10)
            if rev > limit // 10 or (rev == limit // 10 and d > last):
                return 0
            rev = rev * 10 + d
        return sign * rev


def _cdivmod(a: int, b: int) -> tuple[int, int]:
    """Деление как `/` и `%` в C и Java: частное усекается к нулю, остаток со знаком делимого.
    В Python // и % округляют к −∞ (−7 // 10 == −1, −7 % 10 == 3), поэтому эмулируем.
    Это замена одной машинной инструкции; её внутренности в «32-битный» бюджет не считаем."""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q, a - q * b


class NegativeAccumulate:
    def reverse(self, x: int) -> int:
        # Строгий 32-битный вариант: ни одно значение не выходит за [−2³¹, 2³¹ − 1].
        # Отрицательных на одно больше: −2³¹ представимо, +2³¹ — нет. Поэтому abs(x) не берём
        # (в C abs(INT_MIN) — UB), а копим разворот со знаком минус и в конце, если надо, меняем знак.
        neg = x < 0
        if not neg:
            x = -x                      # любое неотрицательное int32 представимо со знаком минус
        min_div, min_last = _cdivmod(INT_MIN, 10)   # −214748364, −8
        rev = 0                         # rev ≤ 0 всё время
        while x:
            x, d = _cdivmod(x, 10)      # d — цифра со знаком минус: 0…−9
            if rev < min_div or (rev == min_div and d < min_last):
                return 0
            rev = rev * 10 + d
        if neg:
            return rev
        return 0 if rev < -INT_MAX else -rev    # −2³¹ нельзя сделать положительным


def _wrap32(v: int) -> int:
    """Как int в Java: оставляем младшие 32 бита, старший — знак (дополнительный код)."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


class Wraparound32:
    def reverse(self, x: int) -> int:
        # Java-трюк: считаем с переполнением (обёртка по модулю 2³²) и проверяем, обратим ли шаг:
        # если (new − d) / 10 != rev, по дороге отвалились старшие биты.
        # В Java переполнение int определено, в C для знаковых — UB, там так писать нельзя.
        # Работает со знаком как есть: цифры отрицательного x отрицательны, abs не нужен.
        rev = 0
        while x:
            x, d = _cdivmod(x, 10)
            new = _wrap32(rev * 10 + d)
            if _cdivmod(_wrap32(new - d), 10)[0] != rev:
                return 0
            rev = new
        return rev


ALL = {
    "StrCompare": StrCompare,
    "StrLexCompare": StrLexCompare,
    "PopPushGuard": PopPushGuard,
    "NegativeAccumulate": NegativeAccumulate,
    "Wraparound32": Wraparound32,
}
