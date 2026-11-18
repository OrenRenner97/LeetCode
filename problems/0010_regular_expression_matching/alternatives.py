"""10. Regular Expression Matching: альтернативные решения.

m = len(s), n = len(p). Шаблон из букв, '.' и 'x*'; совпасть должна вся строка.

| # | Класс                  | Время          | Память  | Идея                                                              |
|---|------------------------|----------------|---------|-------------------------------------------------------------------|
| 0 | Solution (solution.py) | O(m·n)         | O(m·n)  | рекурсия сверху вниз по (i, j) + @cache                           |
| 1 | Backtrack              | O(2^(m+n)) худ.| O(m+n)  | та же рекурсия без кэша — показывает, зачем нужна мемоизация      |
| 2 | TableDP                | O(m·n)         | O(m·n)  | снизу вверх: dp[i][j] — совпадает ли s[i:] с p[j:]                |
| 3 | RowDP                  | O(m·n)         | O(n)    | то же, хранятся только две строки таблицы                         |
| 4 | TokenNFA               | O(m·k)         | O(k)    | шаблон → k токенов (символ, звезда?); множество активных состояний (Томпсон) |
| 5 | Stdlib                 | —              | —       | re.fullmatch: шаблон задачи — валидный Python-regex               |
"""
import re


class Backtrack:
    def isMatch(self, s: str, p: str) -> bool:
        # Без кэша одна и та же пара (i, j) решается заново по каждому пути, которым до неё дошли.
        # На "aaa…ab" против "a*a*…a*c" путей — сочетания: как разложить m букв по звёздам.
        def go(i: int, j: int) -> bool:
            if j == len(p):
                return i == len(s)
            first = i < len(s) and p[j] in (s[i], ".")
            if j + 1 < len(p) and p[j + 1] == "*":
                return go(i, j + 2) or (first and go(i + 1, j))
            return first and go(i + 1, j + 1)
        return go(0, 0)


class TableDP:
    def isMatch(self, s: str, p: str) -> bool:
        # dp[i][j] = s[i:] совпадает с p[j:]. Считаем с конца: dp[m][n] = True (пусто с пустым).
        # Строка i = m нужна: пустой остаток строки совпадает с хвостом вида "x*y*z*".
        m, n = len(s), len(p)
        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[m][n] = True
        for i in range(m, -1, -1):
            for j in range(n - 1, -1, -1):
                first = i < m and p[j] in (s[i], ".")
                if j + 1 < n and p[j + 1] == "*":
                    dp[i][j] = dp[i][j + 2] or (first and dp[i + 1][j])
                else:
                    dp[i][j] = first and dp[i + 1][j + 1]
        return dp[0][0]


class RowDP:
    def isMatch(self, s: str, p: str) -> bool:
        # dp[i][·] зависит только от dp[i][·] (правее) и dp[i + 1][·]: хватает двух строк.
        m, n = len(s), len(p)
        nxt = [False] * (n + 1)          # строка i + 1
        nxt[n] = True                    # для i = m это «пустая строка, пустой шаблон»; дальше перезаписывается
        cur = nxt
        for i in range(m, -1, -1):
            cur = [False] * (n + 1)
            cur[n] = i == m
            for j in range(n - 1, -1, -1):
                first = i < m and p[j] in (s[i], ".")
                if j + 1 < n and p[j + 1] == "*":
                    cur[j] = cur[j + 2] or (first and nxt[j])
                else:
                    cur[j] = first and nxt[j + 1]
            nxt = cur
        return cur[0]


class TokenNFA:
    def isMatch(self, s: str, p: str) -> bool:
        # Шаблон — цепочка токенов (c, star). Состояние — номер токена, который ждём; k — «всё совпало».
        # Перед каждым символом раскрываем ε-переходы: звёздный токен можно пропустить.
        # Символ двигает состояние: обычный токен — на следующий, звёздный — остаётся на месте.
        # Это симуляция НКА Томпсона: никакого перебора путей, все пути идут параллельно в одном множестве.
        tokens = []
        for c in p:
            if c == "*":
                tokens[-1] = (tokens[-1][0], True)
            else:
                tokens.append((c, False))
        k = len(tokens)

        def closure(states: set[int]) -> set[int]:
            out = set()
            for q in states:
                while q not in out:
                    out.add(q)
                    if q < k and tokens[q][1]:
                        q += 1               # пропустить «x*» — ноль повторений
                    else:
                        break
            return out

        states = closure({0})
        for ch in s:
            step = set()
            for q in states:
                if q < k:
                    c, star = tokens[q]
                    if c == ch or c == ".":
                        step.add(q if star else q + 1)
            if not step:
                return False
            states = closure(step)
        return k in states


class Stdlib:
    def isMatch(self, s: str, p: str) -> bool:
        # Синтаксис задачи — подмножество Python-regex. Движок re — backtracking (как Backtrack),
        # но на C и с оптимизациями; от экспоненты в общем случае не защищён.
        return re.fullmatch(p, s) is not None


ALL = {
    "Backtrack": Backtrack,
    "TableDP": TableDP,
    "RowDP": RowDP,
    "TokenNFA": TokenNFA,
    "Stdlib": Stdlib,
}
