"""Вход для нативного Манакера: a — коды элементов, b — коды их отражений (b = a без mirror).

Сравнение «seq[lo] == mirror[seq[hi]]» превращается в «a[lo] == b[hi]» над целыми массивами.
Строки → кодовые точки int32 (через UTF-32, без цикла на Python); отражение — таблица по коду.
Элемент без пары получает код -1, который не равен ни одному коду (коды ≥ 0).
"""
import numpy as np


def encode(seq, mirror) -> tuple[np.ndarray, np.ndarray, bool]:
    if isinstance(seq, str):
        a = np.frombuffer(seq.encode("utf-32-le"), dtype="<i4")
        if mirror is None:
            return a, a, False
        if not all(isinstance(x, str) and len(x) == 1 for pair in mirror.items() for x in pair):
            raise TypeError("для строки mirror должен отображать символ в символ")
        top = max(int(a.max()) if a.size else 0, *(ord(k) for k in mirror)) + 1
        table = np.full(top, -1, dtype=np.int32)
        for k, v in mirror.items():
            table[ord(k)] = ord(v)
        return a, table[a], True
    if mirror is not None:
        raise TypeError("нативные backend'ы поддерживают mirror только для строк; для прочих — backend='python'")
    a = np.asarray(seq)
    if a.ndim != 1 or a.dtype.kind not in "iu":
        raise TypeError("нативные backend'ы принимают строку или одномерный массив целых; для прочих — backend='python'")
    a = np.ascontiguousarray(a, dtype=np.int64)
    return a, a, False
