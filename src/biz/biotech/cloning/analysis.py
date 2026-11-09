"""Рестрикционный анализ и проверка праймеров. Алгоритм: algos.maximal_palindromes (LeetCode 5, Manacher).

Сайт палиндромного фермента — палиндром относительно комплемента. Поэтому сначала за один проход
Manacher находим все палиндромные центры, а потом по словарю проверяем только центры с достаточным
радиусом. Число ферментов в каталоге почти не влияет на время: проверок столько, сколько разных
длин сайтов, и только на палиндромных центрах (в случайной ДНК радиус ≥ 4 у ~1/16 центров).
"""
from collections.abc import Iterable
from itertools import pairwise

from algos import longest_palindrome
from algos.palindromes import maximal_palindromes

from .catalog import COMMON_ENZYMES
from .models import COMPLEMENT, CloningCandidate, Digest, Enzyme, PrimerReport, PrimerVerdict, Site, normalize


def find_sites(
    seq: str, enzymes: Iterable[Enzyme] | None = None, *, circular: bool = False, backend: str | None = None
) -> dict[str, list[Site]]:
    """Все сайты каждого фермента: {имя: [Site, ...]} по возрастанию позиции, включая ферменты без сайтов.

    circular=True — плазмида: сайт может проходить через «начало» последовательности.
    ValueError: недопустимые символы, повтор имени фермента.
    """
    seq = normalize(seq)
    enzymes = list(COMMON_ENZYMES.values() if enzymes is None else enzymes)
    result: dict[str, list[Site]] = {}
    by_length: dict[int, dict[str, list[Enzyme]]] = {}
    for e in enzymes:
        if e.name in result:
            raise ValueError(f"фермент {e.name!r} указан дважды")
        result[e.name] = []
        by_length.setdefault(len(e.site), {}).setdefault(e.site, []).append(e)
    n = len(seq)
    if not n or not enzymes:
        return result

    lengths = sorted(by_length)
    scan = seq
    if circular:  # дописываем начало в конец, чтобы увидеть сайты через «стык» кольца
        tail = lengths[-1] - 1
        scan = (seq * (tail // n + 2))[: n + tail]

    # Только центры с палиндромом не короче самого короткого сайта (~1/16 центров для 4-щепящих):
    # нативный backend отбирает их векторно, и цикл на Python идёт не по 2n радиусам, а по ним.
    # Горячий цикл (~n/16 итераций): только локальные переменные, без атрибутов и вызовов методов.
    tables = [(length, length // 2, by_length[length]) for length in lengths]
    for lo, hi in maximal_palindromes(scan, min_length=lengths[0], mirror=COMPLEMENT, backend=backend):
        radius = hi - lo  # комплементарный палиндром всегда чётный: нуклеотид не комплементарен себе
        middle = (lo + hi) >> 1
        for length, half, table in tables:
            if length > radius:
                break
            start = middle - half
            hits = table.get(scan[start:start + length])
            if hits is None or start >= n:  # start >= n: повтор начала кольца, сайт уже найден в начале
                continue
            for e in hits:
                cut = start + e.cut
                result[e.name].append(Site(e.name, start, cut % n if circular else cut))
    for sites in result.values():
        sites.sort(key=lambda s: s.position)
    return result


def digest(seq: str, enzymes: Iterable[Enzyme], *, circular: bool = False, backend: str | None = None) -> Digest:
    """Полное переваривание смесью ферментов: места разрезов и длины фрагментов (то, что видно на геле).

    Линейная ДНК: k разрезов внутри → k + 1 фрагмент. Кольцевая: k разрезов → k фрагментов,
    0 разрезов → одна кольцевая молекула исходной длины.
    """
    seq = normalize(seq)
    n = len(seq)
    sites = find_sites(seq, enzymes, circular=circular, backend=backend)
    cuts = sorted({s.cut for ss in sites.values() for s in ss if circular or 0 < s.cut < n})
    if not cuts:
        return Digest((), (n,) if n else ())
    if circular:
        frags = [b - a for a, b in pairwise(cuts)] + [n - cuts[-1] + cuts[0]]
    else:
        bounds = [0, *cuts, n]
        frags = [b - a for a, b in pairwise(bounds)]
    return Digest(tuple(cuts), tuple(frags))


def cloning_candidates(
    vector: str, insert: str, mcs: tuple[int, int], enzymes: Iterable[Enzyme] | None = None, *,
    circular_vector: bool = True, backend: str | None = None,
) -> list[CloningCandidate]:
    """Ферменты для вставки фрагмента в вектор: режут вектор ровно один раз, и этот разрез внутри
    полилинкера mcs = [start, end), а вставку не режут вовсе (иначе вставка развалится).
    Отсортированы по месту разреза в полилинкере.
    """
    lo, hi = mcs
    if not 0 <= lo < hi <= len(normalize(vector)):
        raise ValueError(f"полилинкер {mcs} вне вектора")
    enzymes = list(COMMON_ENZYMES.values() if enzymes is None else enzymes)
    in_vector = find_sites(vector, enzymes, circular=circular_vector, backend=backend)
    in_insert = find_sites(insert, enzymes, backend=backend)
    found = [
        CloningCandidate(e, in_vector[e.name][0].cut)
        for e in enzymes
        if len(in_vector[e.name]) == 1 and lo <= in_vector[e.name][0].position and
        in_vector[e.name][0].position + len(e.site) <= hi and not in_insert[e.name]
    ]
    found.sort(key=lambda c: (c.cut, c.enzyme.name))
    return found


def check_primer(primer: str, *, max_stem: int = 6, max_3prime_stem: int = 3,
                 backend: str | None = None) -> PrimerReport:
    """Самокомплементарность праймера: участок, равный своему обратному комплементу, позволяет двум
    копиям праймера слипнуться (self-dimer) и съесть реакцию ПЦР. Особенно опасен участок на 3'-конце:
    полимераза достраивает его, и в продукте появляется димер праймеров.

    SELF_DIMER: самый длинный участок длиннее max_stem или участок на 3'-конце длиннее max_3prime_stem.
    Это быстрый фильтр, а не термодинамика (ΔG): его ставят до дорогого расчёта.
    """
    primer = normalize(primer, "праймер")
    if "N" in primer:
        return PrimerReport(primer, PrimerVerdict.HAS_N, None, 0)
    stem = longest_palindrome(primer, mirror=COMPLEMENT, backend=backend)
    at_3prime = max((e - s for s, e in maximal_palindromes(primer, min_length=2, mirror=COMPLEMENT, backend=backend)
                     if e == len(primer)), default=0)
    length = stem[1] - stem[0] if stem else 0
    risky = length > max_stem or at_3prime > max_3prime_stem
    return PrimerReport(primer, PrimerVerdict.SELF_DIMER if risky else PrimerVerdict.OK, stem, at_3prime)
