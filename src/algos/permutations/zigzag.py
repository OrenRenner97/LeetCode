"""Зигзаг-перестановка последовательности. LeetCode: 6. Zigzag Conversion (обобщённо).

Элементы раскладываются по `rows` строкам «змейкой»: вниз 0, 1, …, rows - 1, затем вверх и снова вниз.
Затем строки читаются подряд. Это перестановка, периодическая по индексу с периодом T:

  mode="zigzag" (LeetCode 6, шифр «изгородь»): края не повторяются: 0 1 2 1 0 1 2 …, T = 2(rows - 1).
  mode="snake"  (snake-драфт, посев по корзинам): края дважды: 0 1 2 2 1 0 0 1 …, T = 2·rows.

В строке i два «потока» индексов с шагом T: прямой i, i + T, … и обратный partner(i), partner(i) + T, …
(partner = T - i для zigzag, T - 1 - i для snake; у краёв zigzag обратного потока нет). Потоки чередуются,
прямой первым. Поэтому перестановка собирается присваиванием в срезы, без Python-цикла по элементам.

Два обхода, оба O(n) копирований на C:
  по строкам  — min(rows, n) итераций, на строку два среза с шагом T;
  по периодам — ceil(n / T) итераций. Вход дополняется пустышками до целого числа периодов:
                тогда каждая строка занимает в выходе блок фиксированной длины, и внутри одного периода
                позиции строк идут с постоянным шагом. Пустышки бывают только в последнем периоде,
                при кодировании они отфильтровываются, при декодировании их место — маска по срезам.
Обход по строкам, пока rows <= n / 30, иначе по периодам (порог — по замерам, см. _BY_ROWS_MAX_SHARE).
"""
from collections.abc import Sequence
from typing import Literal, TypeVar

from .._dispatch import Dispatcher

Mode = Literal["zigzag", "snake"]
S = TypeVar("S")

# Только python: шаг 3 для этой задачи не делали (README задачи 6). Порядок — на случай нативных backend'ов.
_dispatch = Dispatcher("zigzag", priority=("numba", "c", "numpy", "python"))

# Обход по строкам: ~30 ns на элемент + ~1.8 µs на строку. По периодам: ~90 ns на элемент (дополнение,
# фильтр пустышек, сборка) + ~2 µs на период, которых ~n / (2·rows). По строкам выгоднее, пока
# 1.8 µs · rows < 60 ns · n, то есть rows <= n / 30. Замеры n = 10³…10⁶ (README задачи 6, шаг 1.5):
# точка перелома 31 / ~300 / ~3 000 / ~30 000; при rows = n/2 обход по периодам быстрее в 5–8 раз.
_BY_ROWS_MAX_SHARE = 30

_PAD = object()


def zigzag_rows(n: int, rows: int, *, mode: Mode = "zigzag") -> list[int]:
    """Номер строки для каждой позиции 0..n-1. Например, zigzag_rows(7, 3) == [0, 1, 2, 1, 0, 1, 2].

    mode="snake": zigzag_rows(7, 3, mode="snake") == [0, 1, 2, 2, 1, 0, 0] — порядок выбора в snake-драфте.
    ValueError/TypeError: n < 0, rows < 1, неизвестный mode.
    """
    _check_n(n)
    period = _period(rows, mode)
    if period == 0:  # zigzag с одной строкой
        return [0] * n
    top = rows - 1 if mode == "zigzag" else rows
    cycle = [m if m < top else period - m - (mode == "snake") for m in range(period)]
    full, rest = divmod(n, period)
    return cycle * full + cycle[:rest]


def zigzag_order(n: int, rows: int, *, mode: Mode = "zigzag") -> list[int]:
    """Перестановка: позиция p результата zigzag_encode берёт элемент с индексом order[p].

    zigzag_order(7, 3) == [0, 4, 1, 3, 5, 2, 6]. Обратная перестановка — это zigzag_decode.
    """
    _check_n(n)
    return zigzag_encode(range(n), rows, mode=mode, backend="python")


def zigzag_encode(seq: S, rows: int, *, mode: Mode = "zigzag", backend: str | None = None) -> S:
    """Зигзаг-перестановка: элементы построчно. zigzag_encode("PAYPALISHIRING", 3) == "PAHNAPLSIIGYIR".

    Тип результата = тип входа: str, bytes, bytearray, list, tuple, numpy-массив (по первой оси).
    Остальные последовательности (range, …) → list. Пустой вход → пустой результат. Вход не меняется.
    O(n) при любом rows. ValueError/TypeError: rows < 1 или не int, неизвестный mode.
    """
    _period(rows, mode)
    return _dispatch.resolve(backend, len(seq))(seq, rows, mode, False)


def zigzag_decode(seq: S, rows: int, *, mode: Mode = "zigzag", backend: str | None = None) -> S:
    """Обратная перестановка: zigzag_decode(zigzag_encode(x, r), r) == x. Тип результата = тип входа."""
    _period(rows, mode)
    return _dispatch.resolve(backend, len(seq))(seq, rows, mode, True)


def zigzag_split(seq: Sequence[S], rows: int, *, mode: Mode = "zigzag") -> list[list[S]]:
    """Сами строки зигзага: ровно rows списков (лишние строки пустые), в каждом — элементы по порядку.

    zigzag_split("PAYPALISHIRING", 3) → [list("PAHN"), list("APLSIIG"), list("YIR")].
    С mode="snake" это раздача отсортированных элементов по rows корзинам «змейкой».
    """
    period = _period(rows, mode)
    items = list(seq)
    if period == 0:
        return [items]
    out = []
    for i in range(rows):
        j, vert = _partner(i, rows, mode), items[i::period]  # i >= n → срезы пустые: partner(i) > i
        if j is None:
            out.append(vert)
            continue
        back = items[j::period]
        merged = [None] * (len(vert) + len(back))
        merged[::2], merged[1::2] = vert, back
        out.append(merged)
    return out


# --- проверки и геометрия -------------------------------------------------------------------------

def _check_n(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n должен быть int, получено {type(n).__name__}")
    if n < 0:
        raise ValueError(f"n должен быть >= 0, получено {n}")


def _period(rows, mode):
    """Проверяет rows и mode, возвращает период T (0 — тождественная перестановка: zigzag, одна строка)."""
    if mode not in ("zigzag", "snake"):
        raise ValueError(f"mode должен быть 'zigzag' или 'snake', получено {mode!r}")
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise TypeError(f"rows должен быть int, получено {type(rows).__name__}")
    if rows < 1:
        raise ValueError(f"rows должен быть >= 1, получено {rows}")
    return 2 * (rows - 1) if mode == "zigzag" else 2 * rows


def _partner(i, rows, mode):
    """Начало обратного потока строки i или None (у краёв zigzag поток один)."""
    if mode == "snake":
        return 2 * rows - 1 - i
    return 2 * (rows - 1) - i if 0 < i < rows - 1 else None


# --- python backend --------------------------------------------------------------------------------

@_dispatch.register("python")
def _python(seq, rows, mode, inverse):
    n = len(seq)
    period = _period(rows, mode)
    if period == 0 or rows >= n:
        # Тождественная перестановка: zigzag с одной строкой, или в каждой строке ≤ 1 элемента
        # (обратный поток начинается с partner(i) > rows - 1 >= n - 1).
        if isinstance(seq, (str, bytes, tuple)):
            return seq
        return seq.copy() if hasattr(seq, "dtype") else _finish(seq, list(seq))
    if rows * _BY_ROWS_MAX_SHARE <= n:
        return _finish(seq, _by_rows(seq, n, rows, mode, period, inverse))
    periods = -(-n // period)
    if hasattr(seq, "dtype"):  # numpy: перестановку индексов строим по периодам, переставляем на C
        order = _by_periods(range(n), n, rows, mode, period, periods, False)
        if inverse:
            out = seq.copy()
            out[order] = seq
            return out
        return seq[order]
    return _finish(seq, _by_periods(seq, n, rows, mode, period, periods, inverse))


def _by_rows(seq, n, rows, mode, period, inverse):
    if hasattr(seq, "dtype"):  # numpy: срезы и присваивание в срезы — тоже на C
        import numpy as np
        out = np.empty_like(seq)
    else:
        out = [None] * n
    pos = 0  # начало строки i в закодированной последовательности
    for i in range(rows):  # rows < n (иначе перестановка тождественная)
        j = _partner(i, rows, mode)
        if j is None or j >= n:  # один поток: в выходе подряд
            end = pos + len(range(i, n, period))
            if inverse:
                out[i::period] = seq[pos:end]
            else:
                out[pos:end] = seq[i::period]
        else:  # два потока: в выходе через один, прямой первым (он не короче обратного)
            end = pos + len(range(i, n, period)) + len(range(j, n, period))
            if inverse:
                out[i::period] = seq[pos:end:2]
                out[j::period] = seq[pos + 1:end:2]
            else:
                out[pos:end:2] = seq[i::period]
                out[pos + 1:end:2] = seq[j::period]
        pos = end
    return out


def _by_periods(seq, n, rows, mode, period, periods, inverse):
    # Дополненная до periods·T последовательность. Строка в выходе — блок длины periods (один поток)
    # или 2·periods (два потока, через один). Поэтому в одном периоде соседние строки одного потока
    # лежат в выходе с шагом stride = 2·periods: период переносится четырьмя (snake — двумя) срезами.
    total = periods * period
    stride = 2 * periods
    if mode == "zigzag":
        mid_end = periods + stride * (rows - 2)  # блоки: строка 0 | средние строки | строка rows - 1

        def move(rows_side, input_side, p, b, encode):
            o = periods + 2 * p
            if encode:
                rows_side[p] = input_side[b]
                rows_side[o:mid_end:stride] = input_side[b + 1:b + rows - 1]
                rows_side[o + 1:mid_end:stride] = input_side[b + period - 1:b + rows - 1:-1]
                rows_side[mid_end + p] = input_side[b + rows - 1]
            else:
                input_side[b] = rows_side[p]
                input_side[b + 1:b + rows - 1] = rows_side[o:mid_end:stride]
                input_side[b + period - 1:b + rows - 1:-1] = rows_side[o + 1:mid_end:stride]
                input_side[b + rows - 1] = rows_side[mid_end + p]
    else:
        def move(rows_side, input_side, p, b, encode):
            o = 2 * p
            if encode:
                rows_side[o::stride] = input_side[b:b + rows]
                rows_side[o + 1::stride] = input_side[b + period - 1:b + rows - 1:-1]
            else:
                input_side[b:b + rows] = rows_side[o::stride]
                input_side[b + period - 1:b + rows - 1:-1] = rows_side[o + 1::stride]

    if not inverse:
        src = list(seq)
        src += [_PAD] * (total - n)
        out = [_PAD] * total
        for p in range(periods):
            move(out, src, p, p * period, True)
        return [x for x in out if x is not _PAD] if total > n else out
    # Где в дополненном выходе стоят пустышки: прогоняем последний период на флагах (срезы, на C).
    last = (periods - 1) * period
    flags = [False] * n + [True] * (total - n)
    mask = [False] * total
    move(mask, flags, periods - 1, last, True)
    items = iter(seq)
    padded = [_PAD if m else next(items) for m in mask]
    out = [_PAD] * total
    for p in range(periods):
        move(padded, out, p, p * period, False)
    del out[n:]  # пустышки дополняли вход с конца
    return out


def _finish(seq, out):
    if isinstance(seq, str):
        return "".join(out)
    if isinstance(seq, (bytes, bytearray)):
        return type(seq)(out)
    if isinstance(seq, tuple):
        return tuple(out)
    return out  # list, ndarray; range и прочее → list


zigzag_encode.backends = _dispatch.available  # type: ignore[attr-defined]
zigzag_decode.backends = _dispatch.available  # type: ignore[attr-defined]
