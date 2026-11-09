"""Палиндромы в последовательности за O(n). LeetCode: 5. Longest Palindromic Substring (обобщённо).

Всё строится на одном массиве радиусов (Manacher). Центров 2n + 1: на каждом элементе (нечётные
палиндромы) и в каждом промежутке, включая края (чётные). radii[c] — длина самого длинного палиндрома
с центром c; он занимает полуинтервал [(c - L) // 2, (c + L) // 2).

mirror — палиндром «с отображением»: элемент слева должен быть равен mirror[элемент справа].
Для ДНК это обратная комплементарность (GAATTC ↔ комплемент CTTAAG, прочитанный задом наперёд, = GAATTC).
mirror обязан быть инволюцией (mirror[mirror[x]] == x), иначе отражение внутри палиндрома
не работает и O(n) теряется. Элемент без пары в mirror не совпадает ни с чем.
Центр нечётного палиндрома должен переходить сам в себя: в ДНК таких нет, все сайты чётные.
"""
from collections.abc import Hashable, Mapping, Sequence

from .._dispatch import Dispatcher

# benchmarks/longest_palindrome_backends.py: ядра numba и C равны (17–27 ms на 10⁶), numba дешевле
# на входе (ctypes + .ctypes.data) → первая; C — если нет numba. На 20 символах с mirror Python быстрее
# (таблица комплемента + JIT-вызов ~50 µs), с ~200 нативные выигрывают ×5–50 → min_n = 64.
_dispatch = Dispatcher("palindrome_radii", priority=("numba", "c", "python"))

_NO_PAIR = object()  # mirror.get(x, _NO_PAIR) для элемента без пары: не равен ничему


def palindrome_radii(
    seq: Sequence[Hashable], *, mirror: Mapping[Hashable, Hashable] | None = None, backend: str | None = None
) -> list[int]:
    """Массив длины 2·len(seq) + 1: radii[c] — длина максимального палиндрома с центром c.

    Чётное c — центр между seq[c//2 - 1] и seq[c//2] (чётные длины), нечётное c — на seq[c//2].
    Палиндром: seq[(c - radii[c]) // 2 : (c + radii[c]) // 2]. Длина 0 — палиндрома с таким центром нет.
    O(n) времени и памяти.

    Нативные backend'ы (c, numba): строка (mirror — символ → символ) или одномерный массив целых
    без mirror; прочее → TypeError. auto выбирает их только для таких входов.

    ValueError: mirror не инволюция.
    """
    radii = _radii(seq, mirror, backend)
    return radii.tolist() if hasattr(radii, "tolist") else radii


def _radii(seq, mirror, backend):
    """Сырой результат backend'а: list (python) или int64-ndarray (нативные) — его разбираем без цикла."""
    _check_mirror(mirror)
    native_ok = isinstance(seq, str) or (hasattr(seq, "dtype") and mirror is None)
    return _dispatch.resolve(backend, len(seq) if native_ok else 0)(seq, mirror)


def longest_palindrome(
    seq: Sequence[Hashable], *, mirror: Mapping[Hashable, Hashable] | None = None, backend: str | None = None
) -> tuple[int, int] | None:
    """Полуинтервал [start, end) самого длинного палиндрома-подпоследовательности подряд (подстроки).

    Если самых длинных несколько — самый левый. Нет ни одного непустого палиндрома (пустой seq
    или с mirror ничего не совпало) → None. Без mirror у непустого seq ответ всегда есть (длина ≥ 1).
    O(n) времени и памяти при любом входе, в том числе "aaa…a".
    """
    radii = _radii(seq, mirror, backend)
    if hasattr(radii, "argmax"):  # ndarray: argmax возвращает первый максимум → самый левый
        best_c = int(radii.argmax())
        best_len = int(radii[best_c])
        return ((best_c - best_len) // 2, (best_c + best_len) // 2) if best_len else None
    best_c, best_len = 0, 0
    for c, length in enumerate(radii):
        if length > best_len:  # строго больше: при равной длине центр правее → и начало правее
            best_c, best_len = c, length
    if not best_len:
        return None
    return (best_c - best_len) // 2, (best_c + best_len) // 2


def maximal_palindromes(
    seq: Sequence[Hashable], *, min_length: int = 2, mirror: Mapping[Hashable, Hashable] | None = None,
    backend: str | None = None,
) -> list[tuple[int, int]]:
    """Все максимальные (не расширяемые со своего центра) палиндромы длины ≥ min_length.

    По одному на центр, отсортированы по (start, end). Короткие палиндромы внутри длинного
    с тем же центром не перечисляются: они и так следуют из него (срезать края).
    Пример: ДНК-сайты рестрикции и шпильки — палиндромы относительно комплемента длины ≥ 4–6.

    ValueError: min_length < 1.
    """
    if min_length < 1:
        raise ValueError(f"min_length должен быть >= 1, получено {min_length}")
    radii = _radii(seq, mirror, backend)
    if hasattr(radii, "nonzero"):  # ndarray: фильтр и сортировка векторно
        centers = (radii >= min_length).nonzero()[0]
        lengths = radii[centers]
        starts, ends = (centers - lengths) // 2, (centers + lengths) // 2
        order = (starts * (len(radii) + 1) + ends).argsort(kind="stable")
        return list(zip(starts[order].tolist(), ends[order].tolist()))
    found = [((c - length) // 2, (c + length) // 2) for c, length in enumerate(radii) if length >= min_length]
    found.sort()
    return found


def _check_mirror(mirror):
    if mirror is not None:
        for x, y in mirror.items():
            if mirror.get(y, _NO_PAIR) != x:
                raise ValueError(f"mirror должен быть инволюцией: mirror[{x!r}] = {y!r}, но mirror[{y!r}] != {x!r}")


@_dispatch.register("python")
def _python(seq: Sequence[Hashable], mirror: Mapping[Hashable, Hashable] | None) -> list[int]:
    # Виртуальная строка t длины m = 2n + 1: на чётных местах разделители, на нечётных seq[k // 2].
    # Сравниваются только позиции одной чётности (i - k - 1 и i + k + 1), а разделители равны всегда,
    # поэтому сравнивать элементы нужно только при нечётных позициях — и строить t не надо.
    if hasattr(seq, "tolist"):  # numpy: индексация по элементу в Python дорогая, список дешевле
        seq = seq.tolist()
    n = len(seq)
    m = 2 * n + 1
    radii = [0] * m
    c = r = 0  # самый правый известный палиндром: центр c, правая граница r (не включая)
    for i in range(m):
        if i & 1 and mirror is not None:
            x = seq[i >> 1]
            if mirror.get(x, _NO_PAIR) != x:
                continue  # центр не переходит сам в себя: нечётного палиндрома здесь нет (radii = 0)
        k = min(r - i, radii[2 * c - i]) if i < r else 0
        lo, hi = i - k - 1, i + k + 1
        if mirror is None:
            while lo >= 0 and hi < m and (not lo & 1 or seq[lo >> 1] == seq[hi >> 1]):
                lo -= 1
                hi += 1
        else:
            while lo >= 0 and hi < m and (not lo & 1 or seq[lo >> 1] == mirror.get(seq[hi >> 1], _NO_PAIR)):
                lo -= 1
                hi += 1
        k = hi - i - 1
        # Радиус в t на элементе всегда нечётен, в промежутке — чётен; длина в seq равна радиусу в t.
        radii[i] = k
        if i + k > r:
            c, r = i, i + k
    return radii


_dispatch.register_optional("numba", "algos._native.numba_impl", "palindrome_radii_numba", min_n=64)
_dispatch.register_optional("c", "algos._native.c_impl", "palindrome_radii_c", min_n=64)

palindrome_radii.backends = _dispatch.available  # type: ignore[attr-defined]
longest_palindrome.backends = _dispatch.available  # type: ignore[attr-defined]
maximal_palindromes.backends = _dispatch.available  # type: ignore[attr-defined]
