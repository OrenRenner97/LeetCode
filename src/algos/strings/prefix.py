"""Самый длинный общий префикс. LeetCode: 14. Longest Common Prefix.

Отличия от LeetCode-версии:
- любые последовательности одного типа: `str`, `bytes`, `list`, `tuple`; тип результата = тип элементов.
  Элементы списков сравниваются только через `==`, порядок на них не нужен (подойдут и dict);
- пустой набор → `None` (у LeetCode n ≥ 1 гарантировано). Пустой префикс — это "" / b"" / [] / (), а не `None`;
- `sep` — префикс только из целых компонент: ["/usr/lib", "/usr/local"] → "/usr/", а не "/usr/l", как у
  `os.path.commonprefix`. Компонента целая, если у каждого элемента за префиксом конец или `sep`:
  ["/usr/lib", "/usr/lib/x"] → "/usr/lib". Для путей, S3-ключей, имён метрик "a.b.c", списков сегментов;
- принимает любой iterable (генератор тоже) — он читается один раз.

Реализация:
- str/bytes — MinMax из задачи 14: общий префикс всех = общий префикс лексикографических min и max
  (`min`/`max` — 2n сравнений на C). Расхождение min и max ищется бинпоиском по длине через `startswith`:
  log m шагов Python вместо m;
- list/tuple — HorizontalEarlyExit: порядок на элементах может не существовать (dict, смесь типов), поэтому
  только `==`; префикс сужается о каждый элемент, пустой — сразу выход.
"""
from collections.abc import Iterable
from typing import TypeVar

Seq = TypeVar("Seq", str, bytes, list, tuple)

_TYPES = (str, bytes, list, tuple)


def common_prefix(items: Iterable[Seq], *, sep: Seq | object | None = None) -> Seq | None:
    """Самый длинный общий префикс всех элементов `items`; пустой набор → None.

    items: str, bytes, list или tuple — все одного типа. Результат того же типа ("" / [] — если префикса нет).
    sep: разделитель компонент. Для str/bytes — непустая подстрока того же типа; для list/tuple — один элемент.
        Префикс обрезается до последней границы компонент: после него у каждого элемента конец или sep.
    O(S) в худшем случае, S — суммарная длина; для str/bytes основная работа идёт на C.

    TypeError: элементы не str/bytes/list/tuple или разных типов; sep не того типа.
    ValueError: sep — пустая строка.
    """
    seqs = items if isinstance(items, list) else list(items)
    if not seqs:
        return None
    kind = type(seqs[0])
    if kind not in _TYPES:
        raise TypeError(f"элементы должны быть str, bytes, list или tuple, получено {kind.__name__}")
    types = set(map(type, seqs))              # на C: генератор с `type(s) is not kind` стоил ~30% всего вызова
    if len(types) > 1:
        bad = next(t.__name__ for t in types if t is not kind)
        raise TypeError(f"все элементы должны быть одного типа: {kind.__name__} и {bad}")
    text = kind is str or kind is bytes
    if sep is not None and text:
        if type(sep) is not kind:
            raise TypeError(f"sep должен быть {kind.__name__}, получено {type(sep).__name__}")
        if not sep:
            raise ValueError("sep не может быть пустым")

    prefix = _text_prefix(seqs) if text else _seq_prefix(seqs)
    if sep is None or not prefix:
        return prefix
    return _cut_to_component(seqs, prefix, sep, text)


def _text_prefix(seqs):
    lo, hi = min(seqs), max(seqs)
    if hi.startswith(lo):                     # частый случай: все начинаются с min (в т.ч. все равны)
        return lo
    # Инвариант: lo[:good] — префикс hi, lo[:bad] — нет. Для bad = min(len) это так: если len(lo) ≤ len(hi),
    # то lo[:bad] = lo, а hi.startswith(lo) только что не выполнилось; если lo длиннее, но lo < hi,
    # они обязаны различаться в первых len(hi) позициях (иначе hi — префикс lo и hi < lo).
    good, bad = 0, min(len(lo), len(hi))
    while bad - good > 1:
        mid = (good + bad) // 2
        if hi.startswith(lo[:mid]):
            good = mid
        else:
            bad = mid
    return lo[:good]


def _seq_prefix(seqs):
    prefix = seqs[0]
    k = len(prefix)
    for s in seqs:
        if len(s) < k:
            k = len(s)
        i = 0
        while i < k and s[i] == prefix[i]:
            i += 1
        k = i
        if not k:
            break
    return prefix[:k]


def _cut_to_component(seqs, prefix, sep, text):
    k = len(prefix)
    if text:
        w = len(sep)
        if all(len(s) == k or s.startswith(sep, k) for s in seqs):
            return prefix
        # граница — сразу после последнего полного вхождения sep в префиксе
        pos = prefix.rfind(sep)
        return prefix[:pos + w] if pos >= 0 else prefix[:0]
    if all(len(s) == k or s[k] == sep for s in seqs):
        return prefix
    for i in range(k - 1, -1, -1):
        if prefix[i] == sep:
            return prefix[:i + 1]
    return prefix[:0]
