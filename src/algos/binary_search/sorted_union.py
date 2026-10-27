"""k-й элемент и медиана объединения отсортированных последовательностей, без слияния.

LeetCode: 4. Median of Two Sorted Arrays (обобщённо).

Сортированность входа НЕ проверяется по умолчанию: проверка стоит O(n) и съедает весь смысл
O(log). Включается флагом check_sorted=True (например, на данных из внешнего источника).
"""
from bisect import bisect_right
from collections.abc import Sequence
from itertools import pairwise
from numbers import Integral
from typing import Any

from .._dispatch import Dispatcher

# Нативные backend'ы принимают только целочисленные numpy-массивы (_as_int64); всё остальное —
# списки, Decimal, float, строки — уходит в python, даже если backend указан явно.
# benchmarks/median_two_sorted_backends.py:
#   разрез: numba ~4.5 µs против 13–18 µs у python на numpy; C ~11 µs — ctypes (a.ctypes.data ~1.6 µs) дороже ядра;
#   K шардов: C ×5–10 к python; numba медленнее C — typed.List стоит ~2 µs на массив.
_two = Dispatcher("kth_of_two_sorted", priority=("numba", "c", "python"))
_many = Dispatcher("kth_of_many_sorted", priority=("c", "numba", "python"))


def kth_of_two_sorted(a: Sequence[Any], b: Sequence[Any], k: int, *, check_sorted: bool = False,
                      backend: str | None = None) -> Any | None:
    """k-й по возрастанию элемент объединения a и b (k с нуля), как если бы их слили и отсортировали.

    a, b — отсортированные по неубыванию последовательности сравнимых элементов
    (int, float, Decimal, str, кортежи, numpy-массивы). Дубли считаются по отдельности.
    k вне [0, len(a) + len(b)) → None.
    O(log min(len(a), len(b))) по времени, O(1) по памяти.

    Неотсортированный вход без check_sorted: ответ бессмысленный, но исключения нет (см. _cut).
    ValueError: вход не отсортирован (только при check_sorted=True).
    """
    if check_sorted:
        _check_sorted(a, b)
    if not 0 <= k < len(a) + len(b):
        return None
    left_max, _ = _split(a, b, k + 1, backend)
    return left_max


def kth_of_sorted(*arrays: Sequence[Any], k: int, check_sorted: bool = False,
                  backend: str | None = None) -> Any | None:
    """k-й по возрастанию элемент (k с нуля) объединения любого числа отсортированных последовательностей.

    Сам выбирает алгоритм: одна-две непустые → разрез (любые сравнимые, O(log min(m, n))),
    три и больше → kth_of_many_sorted (только целые). k вне диапазона или всё пусто → None.
    Перцентиль p (nearest-rank): k = ceil(p · N) - 1.
    """
    if check_sorted:
        _check_sorted(*arrays)
    nonempty = [arr for arr in arrays if len(arr)]
    if len(nonempty) <= 2:
        a, b = (nonempty + [[], []])[:2]
        return kth_of_two_sorted(a, b, k, backend=backend)
    return kth_of_many_sorted(nonempty, k, backend=backend)


def median_of_sorted(*arrays: Sequence[Any], check_sorted: bool = False, backend: str | None = None) -> Any | None:
    """Медиана объединения отсортированных последовательностей. Все пустые (или их нет) → None.

    Медиана — средний элемент или среднее двух средних; всегда считается как (x + y) / 2, поэтому
    тип результата одинаковый при любой длине: int → float, Decimal → Decimal, float → float.
    Одна или две последовательности: любые сравнимые числа, O(log min(m, n)) — разрез из задачи 4.
    Три и больше: только целые, O(k · log n · log R) — см. kth_of_many_sorted.

    ValueError: вход не отсортирован (при check_sorted=True). TypeError: 3+ последовательности не из целых.
    """
    if check_sorted:
        _check_sorted(*arrays)
    nonempty = [arr for arr in arrays if len(arr)]
    total = sum(map(len, nonempty))
    if total == 0:
        return None
    if len(nonempty) <= 2:
        a, b = (nonempty + [[]])[:2]
        left_max, right_min = _split(a, b, (total + 1) // 2, backend)  # +1: при нечётном total лишний элемент слева
        return (left_max + left_max) / 2 if total % 2 else (left_max + right_min) / 2
    hi = kth_of_many_sorted(nonempty, total // 2, backend=backend)
    lo = hi if total % 2 else kth_of_many_sorted(nonempty, total // 2 - 1, backend=backend)
    return (lo + hi) / 2


def kth_of_many_sorted(arrays: Sequence[Sequence[int]], k: int, *, check_sorted: bool = False,
                       backend: str | None = None) -> int | None:
    """k-й по возрастанию элемент объединения любого числа отсортированных последовательностей ЦЕЛЫХ (k с нуля).

    Бинпоиск по ЗНАЧЕНИЮ: наименьшее x, для которого «элементов <= x» больше k.
    Счёт — bisect в каждой последовательности, поэтому O(len(arrays) · log n · log R),
    где R = max - min. Последовательности не сливаются и не копируются.
    Только целые: шаг «x + 1» для float/Decimal не определён (тип проверяется по краям, а не по всем).
    k вне [0, общая длина) → None.

    TypeError: элементы не целые. ValueError: вход не отсортирован (при check_sorted=True).
    """
    if check_sorted:
        _check_sorted(*arrays)
    nonempty = [arr for arr in arrays if len(arr)]
    if not 0 <= k < sum(map(len, nonempty)):
        return None
    fn = _many.resolve(backend)  # неизвестный backend → BackendUnavailable, даже если вход уйдёт в python
    native = None if fn is _kth_many else _as_int64(nonempty)
    if native is not None:
        return fn(native, k)  # целочисленный dtype уже проверен: isinstance по краям не нужен (~0.5 µs на массив)
    ends = [x for arr in nonempty for x in (arr[0], arr[-1])]
    if not all(isinstance(x, Integral) and not isinstance(x, bool) for x in ends):
        raise TypeError("kth_of_many_sorted работает только с целыми; для двух последовательностей есть kth_of_two_sorted")
    return _kth_many(nonempty, k)


@_many.register("python")
def _kth_many(nonempty: list[Sequence[int]], k: int) -> int:
    ends = [x for arr in nonempty for x in (arr[0], arr[-1])]
    lo, hi = int(min(ends)), int(max(ends))  # int(): numpy-скаляры переполнились бы на (lo + hi)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(_count_le(arr, mid) for arr in nonempty) > k:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _split(a: Sequence[Any], b: Sequence[Any], need: int, backend: str | None) -> tuple[Any, Any | None]:
    fn = _two.resolve(backend)
    native = None if fn is _cut else _as_int64([a, b])
    return fn(*native, need) if native is not None else _cut(a, b, need)


@_two.register("python")
def _cut(a: Sequence[Any], b: Sequence[Any], need: int) -> tuple[Any, Any | None]:
    # Разрез из solution.py, обобщённый с «половины» на любое need: слева ровно need элементов,
    # каждый слева <= каждого справа. Возвращает (max слева, min справа или None, если справа пусто).
    # Вместо ±inf — явные проверки краёв: так работают любые сравнимые типы, а не только числа.
    # Разрез находится ВСЕГДА, даже на неотсортированном входе: «много» в i исключает «мало» в i - 1
    # (a[i-1] > b[j] против b[j] > a[i-1]), поэтому на границе hi никогда не «мало», на lo — не «много»,
    # и при lo == hi условие выполнено. raise ниже недостижим и оставлен как страховка.
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    lo, hi = max(0, need - n), min(need, m)  # j = need - i должен попасть в [0, n]
    while lo <= hi:
        i = (lo + hi) // 2
        j = need - i
        if i > 0 and j < n and a[i - 1] > b[j]:
            hi = i - 1  # из a взяли слишком много
        elif j > 0 and i < m and b[j - 1] > a[i]:
            lo = i + 1  # из a взяли слишком мало
        else:
            left = ([a[i - 1]] if i > 0 else []) + ([b[j - 1]] if j > 0 else [])  # need >= 1 → не пусто
            right = ([a[i]] if i < m else []) + ([b[j]] if j < n else [])
            return max(left), (min(right) if right else None)
    raise AssertionError("недостижимо: разрез существует для любого входа")


def _count_le(arr: Sequence[int], x: int) -> int:
    if hasattr(arr, "searchsorted"):  # numpy: бинпоиск на C, без Python-обращений к элементам
        return int(arr.searchsorted(x, side="right"))
    return bisect_right(arr, x)


def _as_int64(arrays: list[Sequence[Any]]) -> list[Any] | None:
    # Вход для нативных backend'ов: только одномерные C-непрерывные numpy-массивы со знаковыми целыми
    # (int8..int64 → int64; для int64 без копии). Иначе None → python. numpy здесь не импортируется.
    out = []
    for arr in arrays:
        dtype = getattr(arr, "dtype", None)
        if dtype is None or dtype.kind != "i" or arr.ndim != 1 or not arr.flags.c_contiguous:
            return None
        out.append(arr.astype("int64", copy=False))
    return out


def _check_sorted(*arrays: Sequence[Any]) -> None:
    for idx, arr in enumerate(arrays):
        if any(x > y for x, y in pairwise(arr)):
            raise ValueError(f"последовательность №{idx} не отсортирована по неубыванию")


_two.register_optional("numba", "algos._native.numba_impl", "cut_numba")
_two.register_optional("c", "algos._native.c_impl", "cut_c")
_many.register_optional("numba", "algos._native.numba_impl", "kth_many_numba")
_many.register_optional("c", "algos._native.c_impl", "kth_many_c")

kth_of_two_sorted.backends = _two.available  # type: ignore[attr-defined]
kth_of_many_sorted.backends = _many.available  # type: ignore[attr-defined]
