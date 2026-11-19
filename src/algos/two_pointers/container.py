"""Самый большой «контейнер» между двумя линиями. LeetCode: 11. Container With Most Water.

Отличия от LeetCode-версии:
- возвращает саму пару, а не только площадь: `Container(left, right, area)`; подходящей пары нет → `None`
  (меньше двух линий или все пары уже `min_width`). У LeetCode n ≥ 2 гарантировано;
- `xs` — координаты линий, если они стоят не через 1 (столбы вдоль дороги, станции на линии):
  площадь = (xs[j] − xs[i]) · min(h[i], h[j]). Без xs — позиции 0, 1, 2, …;
- `min_width` — только пары шириной не меньше заданной. Два указателя остаются верны: ширина только
  убывает, поэтому, как только пара стала уже `min_width`, все оставшиеся тоже уже — можно остановиться;
- int и float, валидация: длины, неотрицательные конечные высоты, строго возрастающие xs.

Реализация — TwoPointersSkip из задачи 11 (в 5–9 раз быстрее «учебных» двух указателей в CPython): после сдвига
низкой стенки линии не выше неё пропускаются без вычисления площади — дать больше они не могут.
"""
import math
import operator
from collections.abc import Sequence
from itertools import islice
from typing import NamedTuple

Number = int | float


class Container(NamedTuple):
    left: int      # индекс левой линии
    right: int     # индекс правой линии, left < right
    area: Number   # (x[right] − x[left]) · min(h[left], h[right])


def max_container(heights: Sequence[Number], xs: Sequence[Number] | None = None, *,
                  min_width: Number = 0) -> Container | None:
    """Пара линий с наибольшей площадью (x[j] − x[i]) · min(h[i], h[j]).

    heights: высоты ≥ 0 (int или float). xs: координаты, строго возрастают; None — 0, 1, 2, …
    min_width: учитывать только пары с x[j] − x[i] ≥ min_width.
    При равных площадях — одна из оптимальных пар (детерминированно). O(n) время, O(1) доп. память
    (O(n), если на вход пришёл не list: numpy-массив переводится в list — так поэлементный доступ в ~10 раз быстрее).

    TypeError: элементы не числа (bool тоже не принимается). ValueError: длины heights и xs различаются,
        высота < 0 или не конечна, xs не возрастает строго, min_width < 0 или не конечен.
    """
    h, h_ints = _as_list(heights, "heights")
    if h and (min(h) < 0 or not (h_ints or all(map(math.isfinite, h)))):
        bad = next(v for v in h if v < 0 or not math.isfinite(v))
        raise ValueError(f"heights: высоты должны быть конечными и ≥ 0, получено {bad}")
    _check_number("min_width", min_width)
    if min_width < 0 or not math.isfinite(min_width):
        raise ValueError(f"min_width должен быть конечным и ≥ 0, получено {min_width}")
    if xs is None:
        x = range(len(h))                       # индексация range — на C, отдельная ветка в цикле не нужна
    else:
        x, _ = _as_list(xs, "xs")
        if len(x) != len(h):
            raise ValueError(f"len(xs) = {len(x)} не равна len(heights) = {len(h)}")
        if not all(map(operator.lt, x, islice(x, 1, None))):     # NaN тоже не пройдёт: NaN < b — False
            a, b = next((a, b) for a, b in zip(x, x[1:]) if not a < b)
            raise ValueError(f"xs должны строго возрастать, а {a} → {b}")
        if x and not (math.isfinite(x[0]) and math.isfinite(x[-1])):   # при строгом возрастании хватает краёв
            raise ValueError("xs должны быть конечными")

    left, right = 0, len(h) - 1
    # Лучшее держим в локальных переменных, Container создаём один раз в конце: в цикле CPython
    # каждое обращение к атрибуту и создание кортежа стоят заметно (замеры — README задачи 11, шаг 1.5).
    best_area, best_l, best_r = -1, -1, -1
    while left < right:
        width = x[right] - x[left]
        if width < min_width:
            break                               # дальше пары только уже
        hl, hr = h[left], h[right]
        if hl < hr:
            area = width * hl
            if area > best_area:
                best_area, best_l, best_r = area, left, right
            while left < right and h[left] <= hl:   # линии не выше отброшенной стенки ничего не дадут
                left += 1
        else:
            area = width * hr
            if area > best_area:
                best_area, best_l, best_r = area, left, right
            while left < right and h[right] <= hr:
                right -= 1
    return Container(best_l, best_r, best_area) if best_l >= 0 else None


def _as_list(seq, name: str) -> tuple[list, bool]:
    """(список, все ли элементы int). Проверки — через map/set/min на C: поэлементный цикл с isinstance
    стоил бы дороже самого алгоритма."""
    if isinstance(seq, (str, bytes)):
        raise TypeError(f"{name}: ожидается последовательность чисел, получено {type(seq).__name__}")
    out = seq.tolist() if hasattr(seq, "tolist") else list(seq)
    types = set(map(type, out))
    if not types <= {int, float}:
        for v in out:
            _check_number(name, v)                  # подклассы int/float (кроме bool) допустимы
        return out, False
    return out, float not in types


def _check_number(name: str, v) -> None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"{name}: ожидается int или float, получено {type(v).__name__}")
