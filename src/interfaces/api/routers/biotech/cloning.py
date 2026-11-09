from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import AfterValidator, BaseModel, Field, model_validator

from biz.biotech.cloning import COMMON_ENZYMES, Enzyme, check_primer, cloning_candidates, digest, find_sites

from ...errors import BAD_BACKEND
from ...schemas import Backend

router = APIRouter(prefix="/cloning", tags=["biotech/cloning"])

_DNA = r"^[ACGTNacgtn\s]*$"


def _known(names: list[str] | None) -> list[str] | None:
    if names is not None:
        unknown = [n for n in names if n not in COMMON_ENZYMES]
        if unknown:
            raise ValueError(f"нет в каталоге: {unknown}; см. GET /v1/biotech/cloning/enzymes или custom_enzymes")
        if len(set(names)) != len(names):
            raise ValueError("ферменты повторяются")
    return names


Sequence = Annotated[str, Field(pattern=_DNA, max_length=1_000_000,
                                description="ДНК: A, C, G, T, N (неизвестный нуклеотид). Регистр, пробелы и переводы "
                                            "строк не важны. До 10⁶ п.н.")]
EnzymeNames = Annotated[list[str] | None, AfterValidator(_known), Field(
    description="Ферменты из каталога по именам. `null` — весь каталог", examples=[["EcoRI", "BamHI"]])]


class EnzymeIn(BaseModel):
    name: str = Field(description="Имя фермента", examples=["Eco53kI"])
    pattern: str = Field(description="Сайт с местом разреза верхней цепи `^`. Только палиндромные сайты без N",
                         examples=["GAG^CTC"])

    def build(self) -> Enzyme:
        return Enzyme.parse(self.name, self.pattern)

    @model_validator(mode="after")
    def _valid(self):
        self.build()  # ValueError → 422 с объяснением
        return self


class EnzymeOut(BaseModel):
    name: str = Field(description="Имя фермента")
    pattern: str = Field(description="Сайт узнавания, `^` — место разреза верхней цепи")
    ends: Literal["5'", "3'", "blunt"] = Field(description="Концы после разреза: выступающий 5'-, 3'-конец или тупые")
    overhang: str = Field(description="Выступающий одноцепочечный конец. Одинаковый overhang и тип концов → "
                                      "фрагменты сшиваются друг с другом. Пусто для тупых концов")


def _enzyme_out(e: Enzyme) -> EnzymeOut:
    return EnzymeOut(name=e.name, pattern=e.pattern, ends=e.ends.value, overhang=e.overhang)


def _enzymes(names: list[str] | None, custom: list[EnzymeIn]) -> list[Enzyme]:
    chosen = list(COMMON_ENZYMES.values()) if names is None and not custom else [COMMON_ENZYMES[n] for n in names or []]
    return chosen + [c.build() for c in custom]


class _EnzymeChoice(BaseModel):
    enzymes: EnzymeNames = None
    custom_enzymes: list[EnzymeIn] = Field(
        default_factory=list, max_length=500,
        description="Свои ферменты в дополнение к `enzymes`. Если `enzymes` = `null` и есть свои — только свои")

    @model_validator(mode="after")
    def _unique_names(self):
        names = [*(self.enzymes or []), *(c.name for c in self.custom_enzymes)]
        if len(set(names)) != len(names):
            raise ValueError("имена ферментов (каталог + свои) должны быть уникальны")
        return self


class RestrictionMapRequest(_EnzymeChoice):
    sequence: Sequence
    circular: bool = Field(False, description="Кольцевая ДНК (плазмида): сайты могут проходить через начало")
    backend: Backend = None


class SiteOut(BaseModel):
    position: int = Field(description="Начало сайта на верхней цепи, с 0")
    cut: int = Field(description="Разрез верхней цепи перед этой позицией")


class EnzymeMapOut(EnzymeOut):
    sites: list[SiteOut] = Field(description="Все сайты по возрастанию позиции")


class RestrictionMapResponse(BaseModel):
    length: int = Field(description="Длина последовательности, п.н.")
    enzymes: list[EnzymeMapOut] = Field(description="Ферменты в порядке запроса, включая не нашедшие сайтов")
    unique_cutters: list[str] = Field(description="Ферменты ровно с одним сайтом: кандидаты для клонирования")
    non_cutters: list[str] = Field(description="Ферменты без сайтов")
    cuts: list[int] = Field(description="Все места разрезов при одновременной обработке всеми ферментами")
    fragments: list[int] = Field(description="Длины фрагментов при такой обработке (то, что видно на геле), п.н.")


class CandidatesRequest(_EnzymeChoice):
    vector: Sequence
    insert: Sequence
    mcs_start: int = Field(ge=0, description="Начало полилинкера (multiple cloning site) в векторе, с 0")
    mcs_end: int = Field(gt=0, description="Конец полилинкера (не включая)")
    circular_vector: bool = Field(True, description="Вектор кольцевой (обычная плазмида)")
    backend: Backend = None

    @model_validator(mode="after")
    def _mcs(self):
        if not self.mcs_start < self.mcs_end <= len("".join(self.vector.split())):
            raise ValueError("полилинкер должен лежать внутри вектора и быть непустым")
        return self


class CandidateOut(EnzymeOut):
    cut: int = Field(description="Единственный разрез в векторе")


class CandidatesResponse(BaseModel):
    candidates: list[CandidateOut] = Field(description="Подходящие ферменты по месту разреза в полилинкере")


class PrimerCheckRequest(BaseModel):
    primers: list[Annotated[str, Field(pattern=_DNA, min_length=1, max_length=200)]] = Field(
        max_length=10_000, description="Праймеры 5'→3'")
    max_stem: int = Field(6, ge=2, description="Самый длинный допустимый самокомплементарный участок, п.н.")
    max_3prime_stem: int = Field(3, ge=0, description="Допустимый самокомплементарный участок на 3'-конце, п.н.")
    backend: Backend = None


class PrimerOut(BaseModel):
    primer: str = Field(description="Праймер (верхний регистр)")
    verdict: Literal["ok", "self_dimer", "has_n"] = Field(
        description="`self_dimer` — праймер слипается сам с собой, `has_n` — есть неизвестный нуклеотид")
    stem: str | None = Field(description="Самый длинный самокомплементарный участок")
    stem_start: int | None = Field(description="Его начало, с 0")
    stem_3prime: int = Field(description="Длина самокомплементарного участка на 3'-конце")


class PrimerCheckResponse(BaseModel):
    reports: list[PrimerOut] = Field(description="Результаты в порядке запроса")


_PLASMID = "GGATCCAAATTTGAATTCAAACCCGGGTTTAAGCTTAAAGGG"
_MAP_EXAMPLES = {
    "plasmid": {
        "summary": "Плазмида: какие ферменты и где режут",
        "description": "Кольцевая ДНК; ферменты из каталога по именам. В ответе — сайты, единственные резаки и "
                       "фрагменты при обработке всеми тремя сразу.",
        "value": {"sequence": _PLASMID, "circular": True, "enzymes": ["EcoRI", "BamHI", "HindIII"]},
    },
    "custom": {
        "summary": "Свой фермент вместе с каталожным",
        "description": "Eco53kI режет тот же сайт, что SacI, но с тупыми концами.",
        "value": {"sequence": "ttGAGCTCaa", "enzymes": ["SacI"],
                  "custom_enzymes": [{"name": "Eco53kI", "pattern": "GAG^CTC"}]},
    },
}
_CANDIDATE_EXAMPLES = {
    "mcs": {
        "summary": "Чем вырезать место под вставку",
        "description": "Полилинкер с EcoRI, BamHI, HindIII; во вставке есть BamHI → он не подходит.",
        "value": {"vector": "ATATATATAT" "GAATTCGGATCCAAGCTT" "ATATATATAT", "insert": "ATGGCCGGATCCTTTAAA",
                  "mcs_start": 10, "mcs_end": 28},
    },
}
_PRIMER_EXAMPLES = {
    "pair": {
        "summary": "Нормальный праймер и праймер с сайтом EcoRI на 3'-конце",
        "description": "Второй содержит GAATTC на 3'-конце: две копии слипаются и достраиваются полимеразой.",
        "value": {"primers": ["ATGACCATGATTACGCCAAG", "GTAAAACGACGGCCAGTGAATTC"]},
    },
}


@router.get("/enzymes", summary="Каталог ферментов рестрикции")
def list_enzymes() -> list[EnzymeOut]:
    """Ферменты, доступные по имени в остальных ручках: сайт с местом разреза, тип концов и выступающий конец.

    Все сайты палиндромны относительно комплемента — именно это и позволяет искать их одним проходом
    алгоритма Манакера (**LeetCode 5. Longest Palindromic Substring**).
    """
    return [_enzyme_out(e) for e in COMMON_ENZYMES.values()]


@router.post("/restriction-map", summary="Карта сайтов рестрикции и фрагменты", responses=BAD_BACKEND)
def restriction_map(req: Annotated[RestrictionMapRequest, Body(openapi_examples=_MAP_EXAMPLES)]
                    ) -> RestrictionMapResponse:
    """Где каждый фермент режет последовательность, какие режут ровно один раз, какие не режут,
    и какие фрагменты получатся при обработке всеми выбранными ферментами сразу.

    Все палиндромные центры находятся за один проход Манакера с отображением «комплемент»
    (`algos.palindrome_radii`, **LeetCode 5. Longest Palindromic Substring**), сайты проверяются
    только на них. Бизнес-логика: `biz.biotech.cloning`.
    """
    enzymes = _enzymes(req.enzymes, req.custom_enzymes)
    sites = find_sites(req.sequence, enzymes, circular=req.circular, backend=req.backend)
    d = digest(req.sequence, enzymes, circular=req.circular, backend=req.backend)
    return RestrictionMapResponse(
        length=sum(d.fragments),
        enzymes=[EnzymeMapOut(**_enzyme_out(e).model_dump(),
                              sites=[SiteOut(position=s.position, cut=s.cut) for s in sites[e.name]])
                 for e in enzymes],
        unique_cutters=[e.name for e in enzymes if len(sites[e.name]) == 1],
        non_cutters=[e.name for e in enzymes if not sites[e.name]],
        cuts=list(d.cuts),
        fragments=list(d.fragments),
    )


@router.post("/candidates", summary="Ферменты для вставки фрагмента в вектор", responses=BAD_BACKEND)
def find_cloning_candidates(req: Annotated[CandidatesRequest, Body(openapi_examples=_CANDIDATE_EXAMPLES)]
                            ) -> CandidatesResponse:
    """Ферменты, которые режут вектор ровно один раз внутри полилинкера и не режут вставку.

    Это первый вопрос при клонировании: чем открыть вектор, не развалив ни его, ни вставку.
    Алгоритм: **LeetCode 5. Longest Palindromic Substring** (Манакер). Бизнес-логика: `biz.biotech.cloning`.
    """
    found = cloning_candidates(req.vector, req.insert, (req.mcs_start, req.mcs_end),
                               _enzymes(req.enzymes, req.custom_enzymes),
                               circular_vector=req.circular_vector, backend=req.backend)
    return CandidatesResponse(candidates=[CandidateOut(**_enzyme_out(c.enzyme).model_dump(), cut=c.cut)
                                          for c in found])


@router.post("/primer-check", summary="Самокомплементарность праймеров", responses=BAD_BACKEND)
def check_primers(req: Annotated[PrimerCheckRequest, Body(openapi_examples=_PRIMER_EXAMPLES)]) -> PrimerCheckResponse:
    """Ищет в праймерах участки, равные своему обратному комплементу: из-за них две копии праймера
    слипаются (self-dimer). Особенно опасен такой участок на 3'-конце.

    Самый длинный участок — `algos.longest_palindrome` с отображением «комплемент»
    (**LeetCode 5. Longest Palindromic Substring**). Быстрый фильтр перед термодинамическим расчётом.
    Бизнес-логика: `biz.biotech.cloning`.
    """
    out = []
    for p in req.primers:
        r = check_primer(p, max_stem=req.max_stem, max_3prime_stem=req.max_3prime_stem, backend=req.backend)
        out.append(PrimerOut(primer=r.primer, verdict=r.verdict.value,
                             stem=r.primer[r.stem[0]:r.stem[1]] if r.stem else None,
                             stem_start=r.stem[0] if r.stem else None, stem_3prime=r.stem_3prime))
    return PrimerCheckResponse(reports=out)
