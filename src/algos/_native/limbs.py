"""Общие хелперы для нативных реализаций длинной арифметики (массивы uint64)."""
import numpy as np

U64 = 2**64
MAX_GENERIC_BASE = 2**63  # при большем base (кроме 2^64) a + b может переполнить uint64


def supported(base: int) -> bool:
    return base == U64 or 2 <= base <= MAX_GENERIC_BASE


def prepare(a, b, xp=np):
    """→ (A, B): uint64-массивы, len(A) >= len(B)."""
    A = xp.ascontiguousarray(xp.asarray(a, dtype=xp.uint64))
    B = xp.ascontiguousarray(xp.asarray(b, dtype=xp.uint64))
    return (A, B) if A.shape[0] >= B.shape[0] else (B, A)


def finish(out, carry: bool, xp=np):
    """Дописать финальный перенос и срезать ведущие нули (ноль = [0])."""
    if carry:
        return xp.concatenate([out, xp.ones(1, dtype=xp.uint64)])
    if out.shape[0] and int(out[-1]) != 0:  # частый случай: ведущих нулей нет, не сканируем весь массив
        return out
    nz = xp.flatnonzero(out)
    if nz.shape[0] == 0:
        return xp.zeros(1, dtype=xp.uint64)
    return out[: int(nz[-1]) + 1]
