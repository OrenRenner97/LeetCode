"""9. Palindrome Number: альтернативные решения.

d = число цифр (≤ 10). Все решения O(d) по времени: разница в том, выполнен ли follow-up
(«без перевода в строку»), бывает ли ранний выход и сколько стоит одна операция в CPython.

| # | Класс                  | Строка? | Идея                                                                     |
|---|------------------------|---------|--------------------------------------------------------------------------|
| 0 | Solution (solution.py) | да      | str(x) == str(x)[::-1]                                                   |
| 1 | StrOnce                | да      | то же, но строка строится один раз и отрицательные отсекаются сразу      |
| 2 | StrHalf                | да      | сравниваем только половины: s[:h] == s[:-h-1:-1]                         |
| 3 | FullReverse            | нет     | разворачиваем всё число через divmod и сравниваем (в C — переполнение)   |
| 4 | HalfReverse            | нет     | разворачиваем только младшую половину, пока rev < x (официальный ответ)  |
| 5 | PeelEnds               | нет     | сравниваем старшую и младшую цифры, срезаем обе; выход на первом несовпадении |
| 6 | DigitsTwoPointers      | нет     | цифры в список через divmod, два указателя навстречу                     |
"""


class StrOnce:
    def isPalindrome(self, x: int) -> bool:
        # Минус у отрицательного числа есть только слева, поэтому «−121» не палиндром.
        # Отсекаем без строк: дешевле, чем str() и сравнение.
        if x < 0:
            return False
        s = str(x)
        return s == s[::-1]


class StrHalf:
    def isPalindrome(self, x: int) -> bool:
        # Достаточно сравнить первую половину с перевёрнутой второй: средняя цифра нечётной длины ни с чем
        # не сравнивается. Срезы копируют вдвое меньше, но на d ≤ 10 это доли наносекунд.
        if x < 0:
            return False
        s = str(x)
        h = len(s) // 2
        return s[:h] == s[:-h - 1:-1]


class FullReverse:
    def isPalindrome(self, x: int) -> bool:
        # Число — палиндром, если равно своему развороту. В Python int неограничен; в C/Java разворот
        # 32-битного x может переполниться (2147483647 → 7463847412). Переполнившийся разворот палиндромом
        # быть не может, но в C знаковое переполнение — UB: результат сравнения не гарантирован.
        if x < 0:
            return False
        n, rev = x, 0
        while n:
            n, d = divmod(n, 10)
            rev = rev * 10 + d
        return rev == x


class HalfReverse:
    def isPalindrome(self, x: int) -> bool:
        # Разворачиваем младшие цифры, пока разворот не догонит остаток: тогда пройдена половина.
        # Переполнения нет (rev ≤ x), итераций вдвое меньше.
        # Число с нулём на конце (кроме самого 0) — не палиндром: старшая цифра не бывает нулём.
        # Без этой проверки 10 дал бы x = 0, rev = 1 → 1 // 10 == 0 → True.
        if x < 0 or (x % 10 == 0 and x != 0):
            return False
        rev = 0
        while x > rev:
            x, d = divmod(x, 10)
            rev = rev * 10 + d
        # Чётное число цифр: x == rev. Нечётное: средняя цифра ушла в rev, отрезаем её.
        return x == rev or x == rev // 10


class PeelEnds:
    def isPalindrome(self, x: int) -> bool:
        # div = 10^(d−1): x // div — старшая цифра, x % 10 — младшая. Совпали — срезаем обе
        # ((x % div) // 10) и делим div на 100. Выход на первом несовпадении: у случайного x — сразу.
        # Нули внутри (1001 → 00 → div = 1) не теряются, потому что div считается отдельно от x.
        if x < 0:
            return False
        div = 1
        while x // div >= 10:
            div *= 10
        while x:
            if x // div != x % 10:
                return False
            x = (x % div) // 10
            div //= 100
        return True


class DigitsTwoPointers:
    def isPalindrome(self, x: int) -> bool:
        # Как сравнение строки двумя указателями, только «строка» — список цифр (в обратном порядке,
        # для палиндрома это неважно). O(d) памяти, как и у строковых решений.
        if x < 0:
            return False
        digits = []
        while True:
            x, d = divmod(x, 10)
            digits.append(d)
            if not x:
                break
        i, j = 0, len(digits) - 1
        while i < j:
            if digits[i] != digits[j]:
                return False
            i += 1
            j -= 1
        return True


ALL = {
    "StrOnce": StrOnce,
    "StrHalf": StrHalf,
    "FullReverse": FullReverse,
    "HalfReverse": HalfReverse,
    "PeelEnds": PeelEnds,
    "DigitsTwoPointers": DigitsTwoPointers,
}
