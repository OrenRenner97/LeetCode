"""Two Sum на numba: та же хэш-таблица, что в native/c/pair_sum.c, но JIT из Python."""
import numba as nb
import numpy as np

_GOLDEN = np.uint64(0x9E3779B97F4A7C15)


@nb.njit(cache=True, nogil=True)
def _pair_sum(values, target):
    n = values.shape[0]
    bits = 1
    while (1 << bits) < n + n // 2 + 1:
        bits += 1
    mask = np.int64((1 << bits) - 1)
    shift = np.uint64(64 - bits)
    # t[h, 0] = ключ, t[h, 1] = индекс + 1 (0 = пусто). Ключ и индекс рядом: одна проба = один промах кэша.
    t = np.zeros((1 << bits, 2), np.int64)

    for j in range(n):
        x = values[j]
        need = target - x

        # индекс строго int64: смесь uint64 и int64 numba приводит к float64
        h = np.int64((np.uint64(need) * _GOLDEN) >> shift)
        while t[h, 1] != 0:
            if t[h, 0] == need:
                return t[h, 1] - 1, j
            h = (h + 1) & mask

        h = np.int64((np.uint64(x) * _GOLDEN) >> shift)
        while t[h, 1] != 0 and t[h, 0] != x:
            h = (h + 1) & mask
        if t[h, 1] == 0:
            t[h, 0] = x
            t[h, 1] = j + 1
    return -1, -1


def pair_sum_numba(values, target: int):
    i, j = _pair_sum(np.asarray(values, dtype=np.int64), np.int64(target))
    return None if i < 0 else (int(i), int(j))


@nb.njit(cache=True, nogil=True, parallel=True)
def _pairs_batch(values, off, targets, out_i, out_j):
    # prange раздаёт задачи по всем ядрам: это потоки без GIL, без копирования данных.
    for q in nb.prange(targets.shape[0]):
        i, j = _pair_sum(values[off[q]:off[q + 1]], targets[q])
        out_i[q] = i
        out_j[q] = j


def pairs_batch_numba(v, off, t):
    out_i = np.empty(t.shape[0], np.int64)
    out_j = np.empty(t.shape[0], np.int64)
    _pairs_batch(v, off, t, out_i, out_j)
    return out_i, out_j


# ---------- длинная арифметика: carry-select на всех ядрах ----------
# Проход 1 (параллельно): каждый поток складывает свой кусок, считая что переноса на входе нет,
#   и запоминает: перенос на выходе куска и «весь кусок из base-1» (тогда входящий перенос пройдёт насквозь).
# Скан по кускам (последовательно, их ~десятки): настоящий входящий перенос каждого куска.
# Проход 2 (параллельно): куски с входящим переносом прибавляют +1 от начала, пока цифра == base-1.
from .limbs import U64, finish, prepare  # noqa: E402

_U64_MAX = np.uint64(U64 - 1)


@nb.njit(cache=True, nogil=True)
def _add_range(A, B, base, is64, top, lo, hi, out):
    """Сложение разрядов [lo, hi) без входящего переноса. → (перенос наружу, все цифры == top)."""
    nb_ = B.shape[0]
    carry = False
    at = lo < hi
    for k in range(lo, hi):
        x = A[k]
        y = B[k] if k < nb_ else np.uint64(0)
        s = x + y
        if is64:
            g = s < x
        else:
            g = s >= base
            if g:
                s -= base
        if carry:
            if s == top:  # g и «s == top» не бывают одновременно
                s = np.uint64(0)
                g = True
            else:
                s += np.uint64(1)
        out[k] = s
        carry = g
        at = at and s == top
    return carry, at


@nb.njit(cache=True, nogil=True)
def _add_digits_seq(A, B, base, is64):
    # Отдельная непараллельная версия: parallel=True поднимает пул потоков на КАЖДОМ вызове (~1 ms).
    top = _U64_MAX if is64 else base - np.uint64(1)
    out = np.empty(A.shape[0], np.uint64)
    carry, _ = _add_range(A, B, base, is64, top, 0, A.shape[0], out)
    return out, carry


@nb.njit(cache=True, nogil=True, parallel=True)
def _add_digits_par(A, B, base, is64, chunks):
    n = A.shape[0]
    top = _U64_MAX if is64 else base - np.uint64(1)
    out = np.empty(n, np.uint64)
    c_out = np.zeros(chunks, np.bool_)
    all_top = np.zeros(chunks, np.bool_)
    size = (n + chunks - 1) // chunks

    for c in nb.prange(chunks):  # проход 1: куски независимо
        c_out[c], all_top[c] = _add_range(A, B, base, is64, top, c * size, min(n, (c + 1) * size), out)

    c_in = np.zeros(chunks + 1, np.bool_)  # скан по кускам
    for c in range(chunks):
        c_in[c + 1] = c_out[c] or (all_top[c] and c_in[c])

    for c in nb.prange(chunks):  # проход 2: +1 там, где пришёл перенос
        if c_in[c]:
            k, hi = c * size, min(n, (c + 1) * size)
            while k < hi:
                if out[k] == top:
                    out[k] = 0
                    k += 1
                else:
                    out[k] += np.uint64(1)
                    break
    return out, c_in[chunks]


def add_digits_numba(a, b, base: int):
    A, B = prepare(a, b)
    base_u, is64 = np.uint64(0 if base == U64 else base), base == U64
    if A.shape[0] < 1 << 18:
        out, carry = _add_digits_seq(A, B, base_u, is64)
    else:
        out, carry = _add_digits_par(A, B, base_u, is64, nb.get_num_threads() * 4)
    return finish(out, bool(carry))


@nb.njit(cache=True, nogil=True, parallel=True)
def _column_sums(M, is64, chunks):
    N, L = M.shape
    width = 2 * L if is64 else L
    part = np.zeros((chunks, width), np.uint64)
    size = (N + chunks - 1) // chunks
    for c in nb.prange(chunks):
        for r in range(c * size, min(N, (c + 1) * size)):
            for k in range(L):
                x = M[r, k]
                if is64:
                    part[c, 2 * k] += x & np.uint64(0xFFFFFFFF)
                    part[c, 2 * k + 1] += x >> np.uint64(32)
                else:
                    part[c, k] += x
    total = np.zeros(width, np.uint64)
    for c in range(chunks):
        total += part[c]
    return total


@nb.njit(cache=True, nogil=True)
def _column_sums_seq(M, is64):
    N, L = M.shape
    total = np.zeros(2 * L if is64 else L, np.uint64)
    for r in range(N):
        for k in range(L):
            x = M[r, k]
            if is64:
                total[2 * k] += x & np.uint64(0xFFFFFFFF)
                total[2 * k + 1] += x >> np.uint64(32)
            else:
                total[k] += x
    return total


def sum_limbs_numba(M, base: int):
    from .vectorized import column_sums_to_digits

    M = np.ascontiguousarray(M, dtype=np.uint64)
    if M.shape[0] < 1 << 18:  # мало строк: параллельный регион дороже самой работы
        sums = _column_sums_seq(M, base == U64)
    else:
        sums = _column_sums(M, base == U64, nb.get_num_threads() * 4)
    return column_sums_to_digits(sums.tolist(), base)


# ---------- самое длинное окно без повторов ----------
# Ядро работает на сжатых id [0, m) и общем буфере buf, который после себя возвращает в исходное
# состояние (обходит только тронутые ячейки) — так один буфер служит тысячам источников подряд.
from .ids import compact_ids  # noqa: E402


@nb.njit(cache=True, nogil=True)
def _luw_core(ids, lo, hi, k, buf):
    # k == 1: buf[x] = последняя позиция + 1 (0 = не было) → прыжок; k > 1: buf[x] = счётчик → ползём.
    left = lo
    best_s = lo
    best_len = 0
    for r in range(lo, hi):
        x = ids[r]
        if k == 1:
            if buf[x] > left:
                left = buf[x]
            buf[x] = r + 1
        else:
            buf[x] += 1
            while buf[x] > k:
                buf[ids[left]] -= 1
                left += 1
        if r - left + 1 > best_len:
            best_s = left
            best_len = r - left + 1
    for r in range(lo, hi):  # вернуть буфер в нули для следующего источника
        buf[ids[r]] = 0
    return best_s - lo, best_s - lo + best_len


@nb.njit(cache=True, nogil=True)
def _luw_single(ids, m, k):
    return _luw_core(ids, 0, ids.shape[0], k, np.zeros(max(m, 1), np.int64))


def longest_unique_window_numba(seq, max_repeats: int):
    ids, m = compact_ids(seq)
    s, e = _luw_single(ids, m, max_repeats)
    return int(s), int(e)


@nb.njit(cache=True, nogil=True)
def _luw_batch_seq(ids, off, m, k, out_s, out_e):
    buf = np.zeros(max(m, 1), np.int64)
    for q in range(off.shape[0] - 1):
        out_s[q], out_e[q] = _luw_core(ids, off[q], off[q + 1], k, buf)


@nb.njit(cache=True, nogil=True, parallel=True)
def _luw_batch_par(ids, off, m, k, chunks, out_s, out_e):
    nq = off.shape[0] - 1
    size = (nq + chunks - 1) // chunks
    for c in nb.prange(chunks):  # свой буфер на кусок источников: потоки не мешают друг другу
        buf = np.zeros(max(m, 1), np.int64)
        for q in range(c * size, min(nq, (c + 1) * size)):
            out_s[q], out_e[q] = _luw_core(ids, off[q], off[q + 1], k, buf)


def unique_window_batch_numba(values, off, max_repeats: int):
    ids, m = compact_ids(values)
    nq = off.shape[0] - 1
    out_s, out_e = np.zeros(nq, np.int64), np.zeros(nq, np.int64)
    if nq < 1024:
        _luw_batch_seq(ids, off, m, max_repeats, out_s, out_e)
    else:
        # Буфер на кусок = m ячеек; кусков столько, сколько потоков, чтобы память была ~threads × m × 8 байт.
        _luw_batch_par(ids, off, m, max_repeats, nb.get_num_threads(), out_s, out_e)
    return out_s, out_e


# ---------- сжатие id хэш-таблицей: O(n) вместо сортировки в np.unique ----------
# Та же открытая адресация и Fibonacci hashing, что в _pair_sum (LeetCode 1): значение → номер первого появления.
@nb.njit(cache=True, nogil=True)
def factorize_int64(a):
    n = a.shape[0]
    bits = 1
    while (1 << bits) < 2 * n + 1:
        bits += 1
    mask = np.int64((1 << bits) - 1)
    shift = np.uint64(64 - bits)
    keys = np.empty(1 << bits, np.int64)
    slot_id = np.full(1 << bits, -1, np.int64)
    out = np.empty(n, np.int64)
    m = 0
    for i in range(n):
        x = a[i]
        h = np.int64((np.uint64(x) * _GOLDEN) >> shift)
        while slot_id[h] != -1 and keys[h] != x:
            h = (h + 1) & mask
        if slot_id[h] == -1:
            keys[h] = x
            slot_id[h] = m
            m += 1
        out[i] = slot_id[h]
    return out, m
