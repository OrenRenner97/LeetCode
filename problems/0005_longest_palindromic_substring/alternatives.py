"""5. Longest Palindromic Substring: альтернативные решения.

n = длина строки.

| # | Класс                  | Время          | Память | Идея                                                          |
|---|------------------------|----------------|--------|---------------------------------------------------------------|
| 0 | Solution (solution.py) | Θ(n³)          | O(n)   | все подстроки, каждую сравнить с разворотом                   |
| 1 | LongestFirst           | O(n³)          | O(n)   | перебор длин от n вниз, первая найденная — ответ              |
| 2 | DPTable                | Θ(n²)          | O(n²)  | dp[i][j] = s[i] == s[j] and dp[i+1][j-1]                      |
| 3 | ExpandAroundCenter     | O(n²)          | O(1)   | 2n - 1 центров, от каждого расширяемся, пока края равны       |
| 4 | GrowByTwo              | O(n²)*         | O(n)   | ответ, заканчивающийся в i, длиннее прежнего максимум на 2    |
| 5 | HashBinarySearch       | O(n log n)     | O(n)   | бинпоиск по длине (отдельно чётные/нечётные) + хэши           |
| 6 | Manacher               | O(n)           | O(n)   | переиспользуем зеркальный радиус внутри известного палиндрома |

* GrowByTwo делает всего n проверок срезом, сравнение — memcmp на C: на практике очень быстро.
"""


class LongestFirst:
    def longestPalindrome(self, s: str) -> str:
        # Тот же перебор, но с самых длинных: первый найденный палиндром и есть ответ.
        # Худший случай (ответ длины 1) — те же Θ(n³), лучший ("aaaa") — O(n).
        n = len(s)
        for length in range(n, 0, -1):
            for i in range(n - length + 1):
                sub = s[i:i + length]
                if sub == sub[::-1]:
                    return sub
        return ""


class DPTable:
    def longestPalindrome(self, s: str) -> str:
        # dp[i][j]: s[i..j] — палиндром. Строки идут снизу вверх, чтобы dp[i+1] был готов.
        n = len(s)
        dp = [[False] * n for _ in range(n)]
        start, best = 0, 1
        for i in range(n - 1, -1, -1):
            row, below = dp[i], dp[i + 1] if i + 1 < n else None
            row[i] = True
            for j in range(i + 1, n):
                if s[i] == s[j] and (j - i < 3 or below[j - 1]):
                    row[j] = True
                    if j - i + 1 > best:
                        start, best = i, j - i + 1
        return s[start:start + best]


class ExpandAroundCenter:
    def longestPalindrome(self, s: str) -> str:
        # Центр — либо символ (нечётная длина), либо промежуток (чётная): 2n - 1 центров.
        n = len(s)
        start, best = 0, 1
        for center in range(2 * n - 1):
            lo, hi = center // 2, (center + 1) // 2
            while lo >= 0 and hi < n and s[lo] == s[hi]:
                lo -= 1
                hi += 1
            if hi - lo - 1 > best:
                start, best = lo + 1, hi - lo - 1
        return s[start:start + best]


class GrowByTwo:
    def longestPalindrome(self, s: str) -> str:
        # Если палиндром, заканчивающийся в i, длиннее текущего best, то он длиннее
        # ровно на 1 или 2: убрав по символу с краёв, получим палиндром, кончающийся в i - 1.
        # Поэтому на каждом i достаточно проверить ДВЕ подстроки: длины best + 2 и best + 1.
        start, best = 0, 1
        for i in range(1, len(s)):
            lo = i - best - 1
            if lo >= 0:
                sub = s[lo:i + 1]
                if sub == sub[::-1]:
                    start, best = lo, best + 2
                    continue
            lo = i - best
            sub = s[lo:i + 1]
            if sub == sub[::-1]:
                start, best = lo, best + 1
        return s[start:start + best]


_MOD = (1 << 61) - 1
_BASE = 1_000_003


class HashBinarySearch:
    def longestPalindrome(self, s: str) -> str:
        # Внутри одной чётности длина монотонна: есть палиндром длины L → есть и L - 2
        # (срезаем края). Значит, по нечётным и по чётным длинам можно искать бинпоиском.
        # Проверка «есть ли палиндром длины L» — O(n) через полиномиальные хэши
        # строки и её разворота; совпадение хэшей подтверждаем срезом (коллизии).
        n = len(s)
        fwd, rev, pw = [0] * (n + 1), [0] * (n + 1), [1] * (n + 1)
        for i, ch in enumerate(s):
            fwd[i + 1] = (fwd[i] * _BASE + ord(ch)) % _MOD
            rev[i + 1] = (rev[i] * _BASE + ord(s[n - 1 - i])) % _MOD
            pw[i + 1] = pw[i] * _BASE % _MOD

        def find(length: int) -> int:
            p = pw[length]
            for lo in range(n - length + 1):
                hi = lo + length
                h1 = (fwd[hi] - fwd[lo] * p) % _MOD
                h2 = (rev[n - lo] - rev[n - hi] * p) % _MOD  # s[lo:hi] в развёрнутой строке
                if h1 == h2:
                    sub = s[lo:hi]
                    if sub == sub[::-1]:
                        return lo
            return -1

        start, best = 0, 1
        for first in (1, 2):  # нечётные: 1, 3, 5...; чётные: 2, 4, 6...
            lo_k, hi_k = 0, (n - first) // 2  # длина = first + 2k
            found = -1
            while lo_k <= hi_k:
                k = (lo_k + hi_k) // 2
                pos = find(first + 2 * k)
                if pos >= 0:
                    found, lo_k = (k, pos), k + 1
                else:
                    hi_k = k - 1
            if found != -1 and first + 2 * found[0] > best:
                best, start = first + 2 * found[0], found[1]
        return s[start:start + best]


class Manacher:
    def longestPalindrome(self, s: str) -> str:
        # "^#a#b#a#$": все палиндромы становятся нечётными, сторожа ^ и $ избавляют от проверок границ.
        # p[i] — радиус палиндрома с центром i в t (= его длина в s).
        # Внутри самого правого известного палиндрома [c - r, r] зеркальный центр 2c - i
        # уже посчитан: начинаем с min(r - i, p[2c - i]) и расширяемся только дальше r.
        # Правая граница r только растёт, поэтому всего O(n) сравнений.
        t = "^#" + "#".join(s) + "#$"
        p = [0] * len(t)
        c = r = 0
        for i in range(1, len(t) - 1):
            if i < r:
                p[i] = min(r - i, p[2 * c - i])
            while t[i + p[i] + 1] == t[i - p[i] - 1]:
                p[i] += 1
            if i + p[i] > r:
                c, r = i, i + p[i]
        best, center = max((v, i) for i, v in enumerate(p))
        start = (center - best) // 2
        return s[start:start + best]


ALL = {
    "LongestFirst": LongestFirst,
    "DPTable": DPTable,
    "ExpandAroundCenter": ExpandAroundCenter,
    "GrowByTwo": GrowByTwo,
    "HashBinarySearch": HashBinarySearch,
    "Manacher": Manacher,
}
