"""Простые регулярные выражения (`.` и `x*`) без экспоненты. LeetCode: 10. Regular Expression Matching.

Отличия от LeetCode-версии:
- шаблон компилируется один раз (`compile_pattern`), потом проверяет сколько угодно строк;
- линейное время O(len(s) · k / w) на ЛЮБОМ входе, где k — число токенов шаблона, w — разрядность слова:
  НКА Томпсона, множество состояний — битовая маска (shift-and). Никакого перебора путей, поэтому
  нет ReDoS: `re.fullmatch` на «a*a*…a*c» тратит 30 s при 25 символах (README задачи 10), здесь — микросекунды;
- без рекурсии: строки любой длины, не упирается в sys.getrecursionlimit();
- экранирование: `\\.` и `\\*` — буквальные точка и звезда (имена файлов, версии);
- не только строки: `SimplePattern.from_tokens` работает с любыми хэшируемыми элементами (события, токены);
- валидация: `*` в начале шаблона, `**` и `\\` в конце — ValueError, а не «как-нибудь».

Как работает. Шаблон → токены (элемент, звезда?). Бит q маски состояний = «ждём токен q», бит k = «шаблон пройден».
На символе c: оставляем биты токенов, принимающих c (маска masks[c]); обычный токен сдвигается на следующий
бит, звёздный остаётся на месте. Затем ε-замыкание: из звёздного токена можно перейти дальше без символа
(ноль повторений). Всё — операции над одним int, без множеств и словарей состояний.
"""
from collections.abc import Hashable, Iterable, Sequence
from functools import lru_cache

ANY = object()
"""Элемент токена «любой один элемент» для SimplePattern.from_tokens (аналог '.')."""


class SimplePattern:
    """Скомпилированный шаблон. Неизменяемый, потокобезопасный, переиспользуемый."""

    __slots__ = ("pattern", "tokens", "_masks", "_any_mask", "_star_mask", "_start", "_accept")

    def __init__(self, tokens: Sequence[tuple[Hashable, bool]], pattern: str | None = None):
        self.pattern = pattern
        self.tokens: tuple[tuple[Hashable, bool], ...] = tuple(tokens)
        masks: dict[Hashable, int] = {}
        any_mask = star_mask = 0
        for q, (elem, star) in enumerate(self.tokens):
            bit = 1 << q
            if star:
                star_mask |= bit
            if elem is ANY:
                any_mask |= bit
            else:
                masks[elem] = masks.get(elem, 0) | bit
        self._masks = {e: m | any_mask for e, m in masks.items()}   # '.' принимает и буквы шаблона
        self._any_mask = any_mask                                    # элемент, которого нет в шаблоне
        self._star_mask = star_mask
        self._accept = 1 << len(self.tokens)
        self._start = self._closure(1)

    @classmethod
    def from_tokens(cls, tokens: Iterable[tuple[Hashable, bool]]) -> "SimplePattern":
        """Шаблон из готовых токенов (элемент, звезда?); ANY — любой элемент.
        from_tokens([("login", False), (ANY, True), ("payout", False)]) — «вход, что угодно, вывод»."""
        tokens = list(tokens)
        for t in tokens:
            if not (isinstance(t, tuple) and len(t) == 2 and isinstance(t[1], bool)):
                raise TypeError(f"токен: ожидается (элемент, bool), получено {t!r}")
            hash(t[0])
        return cls(tokens)

    def fullmatch(self, seq: Iterable[Hashable]) -> bool:
        """Покрывает ли шаблон ВСЮ последовательность. O(len(seq) · k / w), память O(k / w)."""
        masks, any_mask, star = self._masks, self._any_mask, self._star_mask
        state = self._start
        for c in seq:
            m = state & masks.get(c, any_mask)
            if not m:
                return False                  # ни одного живого состояния: дальше читать незачем
            state = ((m & ~star) << 1) | (m & star)
            if state & star:                  # замыкание нужно, только если стоим на звёздном токене
                state = self._closure(state)
        return bool(state & self._accept)

    # Пошаговый режим: последовательность приходит по одному элементу (поток событий), и хранить её не нужно.
    # Состояние — непрозрачный int: 0 — «мёртвое» (совпасть уже нельзя), дальше можно не читать.
    # fullmatch(seq) == accepts(step(…step(start(), seq[0])…, seq[-1])).

    def start(self) -> int:
        """Состояние до первого элемента."""
        return self._start

    def step(self, state: int, elem: Hashable) -> int:
        """Состояние после ещё одного элемента. O(k / w)."""
        m = state & self._masks.get(elem, self._any_mask)
        if not m:
            return 0
        star = self._star_mask
        state = ((m & ~star) << 1) | (m & star)
        return self._closure(state) if state & star else state

    def accepts(self, state: int) -> bool:
        """Совпадает ли прочитанный до сих пор префикс с шаблоном целиком."""
        return bool(state & self._accept)

    def _closure(self, state: int) -> int:
        """ε-переходы: со звёздного токена можно шагнуть на следующий без символа. Цикл — по длине серии звёзд."""
        star = self._star_mask
        while True:
            nxt = state | ((state & star) << 1)
            if nxt == state:
                return state
            state = nxt

    def __repr__(self) -> str:
        return f"SimplePattern({self.pattern!r})" if self.pattern is not None else f"SimplePattern({self.tokens!r})"


def compile_pattern(pattern: str, *, escape: str | None = "\\") -> SimplePattern:
    """Строка-шаблон → SimplePattern. Синтаксис: буква, '.' — любой символ, 'x*' — ноль или больше x,
    escape + символ — этот символ буквально (r"\\." — точка, r"\\*" — звезда). escape=None — без экранирования.

    Результат кэшируется (lru_cache на 1024 шаблона): повторная компиляция того же шаблона бесплатна.

    TypeError: pattern не str. ValueError: '*' в начале или после другой '*', escape в конце шаблона,
        escape длиннее одного символа или совпадает с '.' / '*'.
    """
    if not isinstance(pattern, str):
        raise TypeError(f"pattern: ожидается str, получено {type(pattern).__name__}")
    if escape is not None and (not isinstance(escape, str) or len(escape) != 1 or escape in ".*"):
        raise ValueError(f"escape: ожидается один символ, кроме '.' и '*', получено {escape!r}")
    return _compile(pattern, escape)


@lru_cache(maxsize=1024)
def _compile(pattern: str, escape: str | None) -> SimplePattern:
    tokens: list[tuple[Hashable, bool]] = []
    can_star = False                          # есть ли токен, к которому может относиться '*'
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == escape:
            if i + 1 == len(pattern):
                raise ValueError(f"{pattern!r}: escape {escape!r} в конце шаблона")
            tokens.append((pattern[i + 1], False))
            can_star = True
            i += 2
            continue
        if c == "*":
            if not can_star:
                where = "в начале шаблона" if i == 0 else "после другой '*'"
                raise ValueError(f"{pattern!r}: '*' в позиции {i} {where} — нечего повторять")
            tokens[-1] = (tokens[-1][0], True)
            can_star = False
        else:
            tokens.append((ANY if c == "." else c, False))
            can_star = True
        i += 1
    return SimplePattern(tokens, pattern)


def is_match(s: str, pattern: str, *, escape: str | None = "\\") -> bool:
    """Покрывает ли pattern всю строку s (LeetCode 10: is_match(s, p, escape=None)).
    Шаблон компилируется с кэшем; для многих строк держите compile_pattern(pattern) у себя."""
    if not isinstance(s, str):
        raise TypeError(f"s: ожидается str, получено {type(s).__name__}")
    return compile_pattern(pattern, escape=escape).fullmatch(s)
