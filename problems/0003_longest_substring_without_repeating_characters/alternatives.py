"""3. Longest Substring Without Repeating Characters: альтернативные решения.

n = len(s), σ = размер алфавита (по условию ~95 печатных ASCII), L = ответ (L <= σ).

| # | Класс                    | Время     | Память | Идея                                                  |
|---|--------------------------|-----------|--------|-------------------------------------------------------|
| 0 | Solution (solution.py)   | O(n·L)    | O(L)   | окно не сжимается: длина = лучший ответ + 1, срез+set |
| 1 | BruteForce               | O(n·L)    | O(L)   | от каждого начала растим set до первого повтора       |
| 2 | WindowSet                | O(n)      | O(L)   | два указателя, левый сдвигаем по одному до удаления повтора |
| 3 | NonShrinkingCounts       | O(n)      | O(σ)   | твоя идея без среза и set: счётчики + число дублей в окне |
| 4 | LastIndex (классика)     | O(n)      | O(σ)   | dict: символ → последняя позиция; левый край прыгает  |
| 5 | LastIndexArray           | O(n)      | O(256) | то же, но список на 256 ячеек вместо dict             |
"""


class BruteForce:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Для каждого начала i расширяем подстроку, пока не встретим повтор.
        # Внутренний цикл не длиннее L+1 (L <= σ), поэтому O(n·L), а не O(n^2).
        n = len(s)
        best = 0
        for i in range(n):
            if best >= n - i:  # от этого начала длиннее уже не найти
                break
            seen = set()
            for j in range(i, n):
                if s[j] in seen:
                    break
                seen.add(s[j])
            best = max(best, len(seen))
        return best


class WindowSet:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Окно [left, right] всегда без повторов. Пришёл повтор — выкидываем символы слева,
        # пока повтор не уйдёт. Каждый символ входит и выходит из set по разу → O(n).
        seen = set()
        left = best = 0
        for right, ch in enumerate(s):
            while ch in seen:
                seen.remove(s[left])
                left += 1
            seen.add(ch)
            best = max(best, right - left + 1)
        return best


class NonShrinkingCounts:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Твоя идея: окно никогда не сжимается. Если окно «плохое» (есть повтор),
        # сдвигаем его целиком (left и right на 1); если «хорошее» — растим.
        # Вместо среза + set держим счётчики символов и число символов с count > 1:
        # проверка «есть ли повтор» стоит O(1), а не O(L).
        count = {}
        dups = 0
        left = 0
        for ch in s:
            count[ch] = count.get(ch, 0) + 1
            if count[ch] == 2:
                dups += 1
            if dups:  # окно плохое → убираем один символ слева (длина окна не меняется)
                out = s[left]
                count[out] -= 1
                if count[out] == 1:
                    dups -= 1
                left += 1
        return len(s) - left  # длина окна = лучший найденный ответ


class LastIndex:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # Помним, где символ был в последний раз. Встретили повтор внутри окна —
        # левый край ПРЫГАЕТ сразу за прошлое вхождение, а не ползёт по одному.
        last = {}
        left = best = 0
        for right, ch in enumerate(s):
            prev = last.get(ch, -1)
            if prev >= left:
                left = prev + 1
            last[ch] = right
            if right - left + 1 > best:
                best = right - left + 1
        return best


class LastIndexArray:
    def lengthOfLongestSubstring(self, s: str) -> int:
        # По условию символы ASCII: список на 256 ячеек вместо dict.
        # Никакого хэширования, просто индекс по коду символа.
        # Для произвольного Unicode не годится (ord до 0x10FFFF).
        last = [-1] * 256
        left = best = 0
        for right, code in enumerate(s.encode("latin-1")):
            if last[code] >= left:
                left = last[code] + 1
            last[code] = right
            if right - left + 1 > best:
                best = right - left + 1
        return best


ALL = {
    "BruteForce": BruteForce,
    "WindowSet": WindowSet,
    "NonShrinkingCounts": NonShrinkingCounts,
    "LastIndex": LastIndex,
    "LastIndexArray": LastIndexArray,
}
