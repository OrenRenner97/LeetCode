"""Векторный Two Sum для numpy и cupy (один код, разные xp).

Без хэш-таблицы, зато без циклов на Python, и всё параллелится на GPU:
  1. стабильно сортируем значения, запоминая исходные индексы;
  2. для каждого j бинарным поиском ищем target - v[j] сразу для всех j;
  3. левый край группы равных значений = самый ранний индекс с этим значением;
  4. пара валидна, если этот индекс < j; берём минимальный такой j.
O(n log n) по времени, O(n) по памяти.
"""
import numpy as np


def _pair_sum(xp, v, target: int, order):
    n = v.shape[0]
    if n < 2:
        return None
    sv = v[order]
    need = target - v
    pos = xp.minimum(xp.searchsorted(sv, need, side="left"), n - 1)
    i = order[pos]
    valid = (sv[pos] == need) & (i < xp.arange(n))
    j = int(xp.argmax(valid))  # первый True; если True нет, вернёт 0
    if not bool(valid[j]):
        return None
    return int(i[j]), j


def pair_sum_numpy(values, target: int):
    v = np.asarray(values, dtype=np.int64)
    return _pair_sum(np, v, target, np.argsort(v, kind="stable"))



# ---------- batch ----------
# Трюк: упаковываем (номер задачи, значение) в один int64-ключ, и тогда ОДИН глобальный
# sort + searchsorted решает все задачи сразу, а задачи не «видят» друг друга.
_BITS = 40
_BIAS = 1 << (_BITS - 1)  # значения сдвигаем в [0, 2^40)


def _pairs_batch(xp, v, off, t, argsort):
    n, q = v.shape[0], t.shape[0]
    out_i = xp.full(q, -1, xp.int64)
    out_j = xp.full(q, -1, xp.int64)
    if n == 0:
        return out_i, out_j
    if int(xp.abs(v).max()) >= _BIAS or int(xp.abs(t).max()) >= _BIAS or q >= 1 << (63 - _BITS):
        raise ValueError("batch: |values|, |targets| должны быть < 2^39, задач < 2^23")

    seg = xp.repeat(xp.arange(q, dtype=xp.int64), xp.diff(off))
    starts = off[:-1][seg]
    key = (seg << _BITS) | (v + _BIAS)
    order = argsort(key)  # стабильно: при равных ключах раньше идёт меньший индекс
    sk = key[order]

    need = t[seg] - v
    ok = xp.abs(need) < _BIAS  # дополнение вне диапазона → точно нет в задаче
    nkey = (seg << _BITS) | (xp.where(ok, need, 0) + _BIAS)
    pos = xp.minimum(xp.searchsorted(sk, nkey, side="left"), n - 1)
    i = order[pos]
    valid = ok & (sk[pos] == nkey) & (i < xp.arange(n))

    jj = xp.nonzero(valid)[0]  # глобальные j по возрастанию → внутри задачи тоже по возрастанию
    if jj.shape[0]:
        s = seg[jj]
        first = xp.ones(jj.shape[0], dtype=bool)
        first[1:] = s[1:] != s[:-1]  # первый валидный j в каждой задаче = минимальный j
        jj, s = jj[first], s[first]
        out_j[s] = jj - starts[jj]
        out_i[s] = i[jj] - starts[jj]
    return out_i, out_j


def pairs_batch_numpy(v, off, t):
    return _pairs_batch(np, v, off, t, lambda k: np.argsort(k, kind="stable"))


# ---------- длинная арифметика: carry-lookahead через scan ----------
# Каждый разряд после a[k] + b[k] находится в одном из трёх состояний:
#   generate  (g): сумма переполнилась — перенос дальше будет В ЛЮБОМ случае;
#   propagate (p): цифра == base-1 — перенос пройдёт насквозь, ЕСЛИ он придёт;
#   kill:          иначе — перенос дальше не пойдёт никогда.
# Перенос в разряд k = «был ли ближайший слева не-propagate разряд генератором».
# Ближайший «стоп» ищем через cumsum + gather (есть и в numpy, и в cupy) — O(n), без цикла по разрядам.
from .limbs import U64, finish, prepare  # noqa: E402


def _add_digits(xp, A, B, base: int):
    n = A.shape[0]
    if n == 0:
        return xp.zeros(1, dtype=xp.uint64)
    Bp = xp.zeros(n, dtype=xp.uint64)
    Bp[: B.shape[0]] = B
    s = A + Bp  # uint64: для base 2^64 переполнение заворачивается, его ловим через s < A
    if base == U64:
        g = s < A
        p = s == xp.uint64(U64 - 1)
    else:
        bu = xp.uint64(base)
        g = s >= bu
        s = xp.where(g, s - bu, s)
        p = s == xp.uint64(base - 1)

    stop = g | ~p  # g и p взаимоисключающие: после переполнения цифра <= base-2
    stop_idx = xp.flatnonzero(stop)
    if stop_idx.shape[0] == 0:
        carry_out = xp.zeros(n, dtype=bool)
    else:
        cnt = xp.cumsum(stop)  # сколько «стопов» в [0, k]
        carry_out = (cnt > 0) & g[stop_idx][xp.maximum(cnt - 1, 0)]  # перенос ИЗ разряда k
    carry_in = xp.concatenate([xp.zeros(1, dtype=bool), carry_out[:-1]])

    out = s + carry_in.astype(xp.uint64)  # для 2^64: MAX + 1 заворачивается в 0 — то, что нужно
    if base != U64:
        out = xp.where(carry_in & p, xp.uint64(0), out)
    return finish(out, bool(carry_out[-1]), xp)


def add_digits_numpy(a, b, base: int):
    return _add_digits(np, *prepare(a, b), base)


# ---------- сумма N чисел: carry-save (отложенный перенос) ----------
# Не складываем числа по одному (N раз прогонять перенос), а суммируем СТОЛБЦЫ.
# Чтобы столбец не переполнил uint64, 64-битный лимб режем на две 32-битные половины:
# сумма N < 2^32 половинок < 2^64. Переносы между столбцами разрешаем один раз в конце (O(L) на Python int).

def column_sums_to_digits(sums, base: int) -> list[int]:
    from algos.arithmetic.digits import to_digits

    if base == U64:  # столбцы — 32-битные половины: [lo0, hi0, lo1, hi1, ...]
        total = sum(int(x) << (32 * k) for k, x in enumerate(sums))
    else:
        total = sum(int(x) * base**k for k, x in enumerate(sums))
    return to_digits(total, base)


def _column_sums(xp, M, base: int):
    if base == U64:
        lo = (M & xp.uint64(0xFFFFFFFF)).sum(axis=0, dtype=xp.uint64)
        hi = (M >> xp.uint64(32)).sum(axis=0, dtype=xp.uint64)
        return xp.stack([lo, hi], axis=1).reshape(-1)  # lo0, hi0, lo1, hi1, ...
    return M.sum(axis=0, dtype=xp.uint64)


def sum_limbs_numpy(M, base: int):
    return column_sums_to_digits(_column_sums(np, np.asarray(M, dtype=np.uint64), base).tolist(), base)


# ---------- самое длинное окно без повторов: накопленный максимум ----------
# prev_k[i] = позиция k-го предыдущего вхождения того же значения (-1, если нет).
# Окно, заканчивающееся в i, не может начинаться раньше prev_k[j] + 1 ни для какого j <= i, поэтому
#     left[i] = max(prev_k[0] + 1, ..., prev_k[i] + 1)      — накопленный максимум (scan),
# длина окна = i - left[i] + 1, ответ — первый максимум. Ни одного цикла по элементам.
from .ids import compact_ids  # noqa: E402


def _cummax(xp, x):
    if xp is np:
        return np.maximum.accumulate(x)
    # В CuPy нет maximum.accumulate: удвоение шага (Hillis–Steele), log2(n) полностью параллельных проходов.
    x = x.copy()
    d = 1
    while d < x.shape[0]:
        x[d:] = xp.maximum(x[d:], x[:-d])
        d *= 2
    return x


def _prev_k(xp, keys, k, argsort):
    n = keys.shape[0]
    order = argsort(keys)  # стабильно: группы равных ключей, внутри — по возрастанию позиции
    sk = keys[order]
    prev = xp.full(n, -1, dtype=xp.int64)
    if n > k:
        same = sk[k:] == sk[:-k]  # k шагов назад в той же группе = k-е предыдущее вхождение
        prev[order[k:]] = xp.where(same, order[:-k], -1)
    return prev


def _np_stable(k):
    return np.argsort(k, kind="stable")


def unique_window_numpy(seq, max_repeats: int, xp=np, argsort=_np_stable):
    ids, _ = compact_ids(seq)
    n = ids.shape[0]
    if n == 0:
        return 0, 0
    ids = xp.asarray(ids)
    left = _cummax(xp, _prev_k(xp, ids, max_repeats, argsort) + 1)
    length = xp.arange(n) - left + 1
    end = int(xp.argmax(length))  # первый максимум → самое левое окно
    return int(left[end]), end + 1


def unique_window_batch_numpy(values, off, max_repeats: int, xp=np, lexsort=np.lexsort):
    ids, _ = compact_ids(values)
    off = xp.asarray(off)
    nq, n = off.shape[0] - 1, ids.shape[0]
    out_s, out_e = xp.zeros(nq, xp.int64), xp.zeros(nq, xp.int64)
    if n == 0:
        return out_s, out_e
    ids = xp.asarray(ids)
    seg = xp.repeat(xp.arange(nq, dtype=xp.int64), xp.diff(off))
    starts = off[:-1][seg]
    pos = xp.arange(n, dtype=xp.int64)

    # Ключ (источник, значение): одинаковые значения разных источников не должны видеть друг друга.
    keys = (seg << 32) | ids
    prev = _prev_k(xp, keys, max_repeats, lambda k: lexsort(xp.stack([pos, k])))
    # Накопленный максимум идёт через границы источников, но значения из прошлых источников
    # всегда < начала текущего, поэтому max с началом источника всё исправляет.
    left = xp.maximum(starts, _cummax(xp, prev + 1))
    length = pos - left + 1

    # Первый максимум в каждом источнике: сортируем по (источник, -длина, позиция), берём первые.
    order = lexsort(xp.stack([pos, -length, seg]))
    s = seg[order]
    first = xp.ones(n, dtype=bool)
    first[1:] = s[1:] != s[:-1]
    best = order[first]
    q = seg[best]
    out_s[q] = left[best] - starts[best]
    out_e[q] = best - starts[best] + 1
    return out_s, out_e
