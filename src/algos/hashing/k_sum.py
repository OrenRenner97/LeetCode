"""Все различные наборы из k чисел с заданной суммой. LeetCode: 15. 3Sum (k = 3, target = 0), 18. 4Sum, 1. Two Sum (k = 2).

Отличия от LeetCode-версии:
- любое `k ≥ 1` и любая `target`; по умолчанию — тройки с нулевой суммой;
- ответ детерминирован: каждый набор — кортеж по возрастанию, список отсортирован лексикографически;
- только целые (int, numpy-целые): у float сумма неточна, `0.1 + 0.2 - 0.3 != 0`,
  и ответ зависел бы от порядка сложения. Нужны дроби — умножьте на 10^d (копейки, а не рубли);
- нет набора — пустой список (это нормальный ответ, а не ошибка); k > n — тоже пустой.

Реализация — CounterValues из задачи 15 (лучшая на всех входах среди чистого Python, ×28 к двум указателям на
повторах): ответ зависит только от различных значений и их кратностей, поэтому перебор идёт по u различным
значениям, а не по n позициям. Наборы строятся по возрастанию: первое значение фиксируется, остаток (k − 1)
ищется рекурсивно среди значений не меньше него, k = 2 — поиск дополнения в словаре (Two Sum).
Время O(n + u^(k−1)), где u — число различных значений; для k = 3 — O(n + u²).
"""
import operator
from bisect import bisect_left
from collections import Counter
from collections.abc import Iterable


def k_sum(values: Iterable[int], target: int = 0, *, k: int = 3) -> list[tuple[int, ...]]:
    """Все различные наборы из k элементов `values` (разных позиций) с суммой `target`.

    Набор — кортеж значений по возрастанию; одинаковые наборы значений не повторяются, даже если собираются
    из разных позиций. Список отсортирован лексикографически.

    >>> k_sum([-1, 0, 1, 2, -1, -4])
    [(-1, -1, 2), (-1, 0, 1)]
    >>> k_sum([1, 0, -1, 0, -2, 2], k=4)
    [(-2, -1, 1, 2), (-2, 0, 0, 2), (-1, 0, 0, 1)]

    TypeError: элементы, target или k — не целые (bool и float тоже; numpy-целые можно). ValueError: k < 1.
    """
    target = _as_int("target", target)
    k = _as_int("k", k)
    if k < 1:
        raise ValueError(f"k должно быть ≥ 1, получено {k}")
    if isinstance(values, (str, bytes)):
        raise TypeError(f"values: ожидаются целые числа, получено {type(values).__name__}")
    items = values.tolist() if hasattr(values, "tolist") else list(values)
    if not set(map(type, items)) <= {int}:              # проверка на C: set типов, а не isinstance в цикле
        items = [_as_int("values", v) for v in items]

    if k > len(items):
        return []
    cnt = Counter(items)
    vals = sorted(cnt)
    res: list[tuple[int, ...]] = []
    if k == 1:
        return [(target,)] if target in cnt else []
    _search(vals, cnt, 0, target, k, (), res)
    return res


def _search(vals: list[int], cnt: dict[int, int], start: int, target: int, k: int,
            prefix: tuple[int, ...], res: list) -> None:
    """Наборы из k значений vals[start:] (с учётом оставшихся кратностей в cnt) с суммой target."""
    lo, hi = vals[start], vals[-1]
    if lo * k > target or hi * k < target:              # даже k минимальных/максимальных не дотягивают
        return
    if k == 2:
        # Two Sum по различным значениям: b ≤ c = target − b. b меньше target − max даёт c > max — пропускаем
        # бинпоиском. Кратность нужна, только если значение берётся второй раз (b == c или b уже в prefix).
        get = cnt.get
        for i in range(max(start, bisect_left(vals, target - hi, start)), len(vals)):
            b = vals[i]
            c = target - b
            if c < b:
                break
            if b == c:
                if get(b, 0) >= 2:
                    res.append(prefix + (b, c))
            elif get(b, 0) >= 1 and get(c, 0) >= 1:
                res.append(prefix + (b, c))
        return
    for i in range(start, len(vals)):
        a = vals[i]
        if a * k > target:                              # дальше все значения ≥ a — сумма только больше
            break
        if a + (k - 1) * hi < target:                   # даже с максимумами не дотянуть — следующее a
            continue
        cnt[a] -= 1                                     # a занято: для остатка его осталось на 1 меньше
        if cnt[a] > 0:
            _search(vals, cnt, i, target - a, k - 1, prefix + (a,), res)
        elif i + 1 < len(vals):
            _search(vals, cnt, i + 1, target - a, k - 1, prefix + (a,), res)
        cnt[a] += 1


def _as_int(name: str, v) -> int:
    """int и всё, что честно им является (numpy-целые: `__index__`); bool и float — нет."""
    if isinstance(v, bool) or not hasattr(type(v), "__index__"):
        raise TypeError(f"{name}: ожидается целое, получено {type(v).__name__}")
    return operator.index(v)
