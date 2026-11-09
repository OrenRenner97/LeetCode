import re
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C"}  # N (неизвестный нуклеотид) пары не имеет
_DNA = re.compile("[ACGTN]*")


def reverse_complement(seq: str) -> str:
    return "".join(COMPLEMENT.get(b, "N") for b in reversed(seq))


def normalize(seq: str, what: str = "последовательность") -> str:
    """Верхний регистр (строчные буквы в геномах — «маскированные» повторы, для нас те же нуклеотиды),
    без пробелов и переводов строк. Допустимы только A, C, G, T и N."""
    seq = seq.upper()
    if not _DNA.fullmatch(seq):  # регулярка на C быстрее set(seq); пробелы убираем, только если они есть
        seq = "".join(seq.split())
    if not _DNA.fullmatch(seq):
        bad = set(seq) - set("ACGTN")
        raise ValueError(f"{what}: недопустимые символы {''.join(sorted(bad))!r}, ожидаются A, C, G, T, N")
    return seq


class Ends(Enum):
    FIVE_PRIME = "5'"   # «липкие» концы с выступающим 5'-концом (EcoRI: G^AATTC → AATT)
    THREE_PRIME = "3'"  # выступающий 3'-конец (PstI: CTGCA^G → TGCA)
    BLUNT = "blunt"     # тупые концы (EcoRV: GAT^ATC)


@dataclass(frozen=True)
class Enzyme:
    """Фермент рестрикции II типа с палиндромным сайтом узнавания.

    site — сайт на верхней цепи, cut — после скольких нуклеотидов сайта режется верхняя цепь.
    Сайт палиндромен (равен своему обратному комплементу), поэтому нижняя цепь режется
    симметрично: после len(site) - cut нуклеотидов, если читать её 5'→3'.
    """
    name: str
    site: str
    cut: int

    def __post_init__(self):
        site = normalize(self.site, f"сайт {self.name}")
        if "N" in site:
            raise ValueError(f"{self.name}: вырожденные сайты (с N) не поддерживаются")
        if not site or len(site) % 2:
            raise ValueError(f"{self.name}: сайт {site!r} нечётной длины не может быть палиндромом ДНК")
        if site != reverse_complement(site):
            raise ValueError(f"{self.name}: сайт {site!r} не палиндромен (обратный комплемент "
                             f"{reverse_complement(site)!r}); такие ферменты не поддерживаются")
        if not 0 <= self.cut <= len(site):
            raise ValueError(f"{self.name}: место разреза {self.cut} вне сайта длины {len(site)}")
        object.__setattr__(self, "site", site)

    @classmethod
    def parse(cls, name: str, pattern: str) -> "Enzyme":
        """'G^AATTC' → Enzyme('EcoRI', 'GAATTC', cut=1)."""
        if pattern.count("^") != 1:
            raise ValueError(f"{name}: в записи сайта {pattern!r} должен быть ровно один '^' (место разреза)")
        return cls(name, pattern.replace("^", ""), pattern.index("^"))

    @property
    def pattern(self) -> str:
        return f"{self.site[:self.cut]}^{self.site[self.cut:]}"

    @property
    def ends(self) -> Ends:
        half = len(self.site) // 2
        if self.cut < half:
            return Ends.FIVE_PRIME
        return Ends.BLUNT if self.cut == half else Ends.THREE_PRIME

    @property
    def overhang(self) -> str:
        """Выступающий одноцепочечный конец. Одинаковый overhang и тип концов → концы совместимы
        (BamHI G^GATCC и BglII A^GATCT оба дают GATC и сшиваются друг с другом)."""
        a, b = sorted((self.cut, len(self.site) - self.cut))
        return self.site[a:b]


class Site(NamedTuple):  # NamedTuple, а не frozen dataclass: создаётся в 4 раза быстрее, а сайтов — десятки тысяч
    enzyme: str
    position: int  # начало сайта узнавания на верхней цепи (0-based)
    cut: int       # разрез верхней цепи: между cut - 1 и cut (для кольцевой ДНК — по модулю длины)


@dataclass(frozen=True)
class Digest:
    cuts: tuple[int, ...]       # уникальные места разрезов, по возрастанию
    fragments: tuple[int, ...]  # длины фрагментов в порядке по молекуле (для кольца — начиная с первого разреза)


@dataclass(frozen=True)
class CloningCandidate:
    enzyme: Enzyme
    cut: int  # единственный разрез в векторе (внутри полилинкера)


class PrimerVerdict(Enum):
    OK = "ok"
    SELF_DIMER = "self_dimer"  # длинный самокомплементарный участок: праймер слипается сам с собой
    HAS_N = "has_n"            # в праймере неизвестный нуклеотид


@dataclass(frozen=True)
class PrimerReport:
    primer: str
    verdict: PrimerVerdict
    stem: tuple[int, int] | None  # самый длинный самокомплементарный участок [start, end)
    stem_3prime: int              # длина самокомплементарного участка, заканчивающегося на 3'-конце
