"""Обёртка ctypes над native/c (собирается через `make -C native`)."""
import ctypes
from pathlib import Path

import numpy as np

_lib = ctypes.CDLL(str(Path(__file__).with_name("libalgos.so")))  # OSError, если не собрана

_i64p = ctypes.POINTER(ctypes.c_int64)
# c_void_p + v.ctypes.data (просто int) вместо POINTER + data_as(): data_as() стоит ~5 µs на вызов.
_lib.pair_sum.argtypes = [ctypes.c_void_p, ctypes.c_int64, ctypes.c_int64, _i64p, _i64p]
_lib.pair_sum.restype = ctypes.c_int


def pair_sum_c(values, target: int):
    v = np.ascontiguousarray(values, dtype=np.int64)
    i, j = ctypes.c_int64(), ctypes.c_int64()
    # ctypes отпускает GIL на время вызова, поэтому потоки Python реально работают параллельно.
    rc = _lib.pair_sum(v.ctypes.data, v.shape[0], target, ctypes.byref(i), ctypes.byref(j))
    if rc < 0:
        raise MemoryError("pair_sum: не удалось выделить хэш-таблицу")
    return (i.value, j.value) if rc else None


# ---------- длинная арифметика (native/c/digits.c) ----------
from .limbs import U64, finish, prepare  # noqa: E402

_lib.add_digits_u64.argtypes = [ctypes.c_void_p, ctypes.c_int64, ctypes.c_void_p, ctypes.c_int64,
                                ctypes.c_uint64, ctypes.c_void_p]
_lib.add_digits_u64.restype = ctypes.c_int


def add_digits_c(a, b, base: int):
    A, B = prepare(a, b)
    out = np.empty(A.shape[0], dtype=np.uint64)
    carry = _lib.add_digits_u64(A.ctypes.data, A.shape[0], B.ctypes.data, B.shape[0],
                                0 if base == U64 else base, out.ctypes.data)
    return finish(out, bool(carry))


# ---------- самое длинное окно без повторов (native/c/unique_window.c) ----------
from .ids import compact_ids  # noqa: E402

_lib.longest_unique_window.argtypes = [ctypes.c_void_p, ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, _i64p, _i64p]
_lib.longest_unique_window.restype = ctypes.c_int


def longest_unique_window_c(seq, max_repeats: int):
    ids, m = compact_ids(seq)
    ids = np.ascontiguousarray(ids)
    s, e = ctypes.c_int64(), ctypes.c_int64()
    if _lib.longest_unique_window(ids.ctypes.data, ids.shape[0], m, max_repeats, ctypes.byref(s), ctypes.byref(e)) < 0:
        raise MemoryError("longest_unique_window: не удалось выделить буфер")
    return s.value, e.value
