from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from biz.infra.rowkeys import KeyOverflow, KeyScheme, compare_sequential, decode, encode

from ...errors import ErrorResponse

router = APIRouter(prefix="/rowkeys", tags=["infra/rowkeys"])

_BAD_RANGE = {400: {"model": ErrorResponse,
                   "description": "id пачки не помещаются в схему: больше 10^width − 1 или ключ переполняет колонку"}}

Storage = Literal["int32", "int64", "uint64", "string"]


class SchemeIn(BaseModel):
    storage: Storage = Field("int64", description="Тип колонки ключа. `string` — строка из `width` цифр "
                                                  "(лексикографический порядок = числовой)")
    width: int | None = Field(None, ge=1, le=40, description="Ширина ключа в цифрах, id от 0 до 10^width − 1. "
                                                             "По умолчанию — безопасная для колонки: int32 → 9, "
                                                             "int64 → 18, uint64 → 19, string → 20")
    reverse: bool = Field(True, description="`true` — развёрнутый ключ (цифры id задом наперёд), "
                                            "`false` — прямой (сам id)")

    def build(self) -> KeyScheme:
        return KeyScheme(self.storage, self.width, self.reverse)


class SchemeOut(BaseModel):
    storage: Storage = Field(description="Тип колонки ключа")
    width: int = Field(description="Ширина ключа в цифрах (с учётом значения по умолчанию)")
    reverse: bool = Field(description="Развёрнутый ли ключ")
    safe: bool = Field(description="Любой id из [0, 10^width − 1] даёт ключ, который влезает в колонку. "
                                   "`false` — часть id получит ошибку переполнения")


def _scheme_out(s: KeyScheme) -> SchemeOut:
    return SchemeOut(storage=s.storage, width=s.width, reverse=s.reverse, safe=s.safe)


class EncodeRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=10_000, description="id строк (неотрицательные целые)")
    scheme: SchemeIn = Field(default_factory=SchemeIn, description="Схема ключа")


class KeyFailure(BaseModel):
    id: str = Field(description="id, для которого ключ не построен (строкой: id может быть больше 2^53)")
    error: str = Field(description="Причина: id вне диапазона схемы или переполнение колонки")


class EncodeResponse(BaseModel):
    scheme: SchemeOut = Field(description="Схема, по которой строились ключи")
    keys: list[str | None] = Field(description="Ключ для каждого id в том же порядке; строкой, потому что int64 "
                                               "больше 2^53 теряет точность в JavaScript. `null` — см. `errors`")
    errors: list[KeyFailure] = Field(description="id, для которых ключ не построен")


class DecodeRequest(BaseModel):
    keys: list[str] = Field(min_length=1, max_length=10_000, description="Ключи строкой, как их вернул `encode`")
    scheme: SchemeIn = Field(default_factory=SchemeIn, description="Схема ключа — та же, что при кодировании")


class DecodeResponse(BaseModel):
    ids: list[str | None] = Field(description="id для каждого ключа (строкой); `null` — ключ не той формы")


class HotspotRequest(BaseModel):
    start: int = Field(ge=0, description="Первый id пачки")
    count: int = Field(ge=1, le=1_000_000, description="Сколько id подряд пишется")
    regions: int = Field(16, ge=1, le=4096, description="На сколько равных регионов (шардов) заранее разбита таблица")
    scheme: SchemeIn = Field(default_factory=SchemeIn, description="Колонка и ширина ключа; поле `reverse` "
                                                                    "игнорируется — сравниваются оба варианта")


class LoadOut(BaseModel):
    loads: list[int] = Field(description="Сколько записей попало в каждый регион")
    hottest_share: float = Field(description="Доля самого нагруженного региона: 1.0 — всё в одном (hotspot)")
    skew: float = Field(description="Максимум / среднее по регионам: 1.0 — идеально ровно")
    regions_touched: int = Field(description="Сколько регионов задействовано. При записи — больше лучше; "
                                             "при чтении этой же пачки — столько регионов обойдёт запрос")


class HotspotResponse(BaseModel):
    direct: LoadOut = Field(description="Прямой ключ (сам id)")
    reversed: LoadOut = Field(description="Развёрнутый ключ")


def _load(r) -> LoadOut:
    return LoadOut(loads=list(r.loads), hottest_share=round(r.hottest_share, 4), skew=round(r.skew, 4),
                   regions_touched=r.regions_touched)


_ENCODE_EXAMPLES = {
    "sequential": {
        "summary": "Подряд идущие заказы → развёрнутые ключи int64",
        "description": "Соседние id получают ключи с разной первой цифрой и попадают в разные регионы.",
        "value": {"ids": [1000000001, 1000000002, 1000000003]},
    },
    "overflow": {
        "summary": "Небезопасная ширина: 19 цифр под int64",
        "description": "id на …99 даёт ключ 9.9·10¹⁸ > 2⁶³ − 1 — ровно переполнение из LeetCode 7.",
        "value": {"ids": [1000000009, 1000000099], "scheme": {"storage": "int64", "width": 19}},
    },
    "collisions": {
        "summary": "Строковый ключ ширины 4: 12, 120 и 1200 не сливаются",
        "value": {"ids": [12, 120, 1200], "scheme": {"storage": "string", "width": 4}},
    },
}
_DECODE_EXAMPLES = {
    "int64": {"summary": "Ключи обратно в id",
              "value": {"keys": ["100000000100000000", "200000000100000000"]}},
}
_HOTSPOT_EXAMPLES = {
    "orders": {
        "summary": "100 000 новых заказов, 16 регионов",
        "description": "Прямой ключ — всё в одном регионе, развёрнутый — ровно по всем.",
        "value": {"start": 1000000000, "count": 100000, "regions": 16},
    },
}


@router.post("/encode", summary="Ключи строк для id")
def encode_rowkeys(req: Annotated[EncodeRequest, Body(openapi_examples=_ENCODE_EXAMPLES)]) -> EncodeResponse:
    """Строит ключ строки для каждого id: прямой или развёрнутый (цифры id задом наперёд в фиксированной ширине).

    Развёрнутый ключ — приём против hotspot'а в HBase/Bigtable: младшая, самая быстро меняющаяся цифра id
    становится первой. Ширина нужна для обратимости (иначе 12 и 120 дают одно 21), проверка колонки — против
    переполнения. Алгоритм: **LeetCode 7. Reverse Integer** → `algos.reverse_digits`. Бизнес-логика:
    `biz.infra.rowkeys`. Ошибки отдельных id — в `errors`, а не HTTP-кодом.
    """
    scheme = req.scheme.build()
    keys, errors = [], []
    for i in req.ids:
        try:
            keys.append(str(encode(i, scheme)))
        except (KeyOverflow, ValueError) as e:
            keys.append(None)
            errors.append(KeyFailure(id=str(i), error=str(e)))
    return EncodeResponse(scheme=_scheme_out(scheme), keys=keys, errors=errors)


@router.post("/decode", summary="id по ключам")
def decode_rowkeys(req: Annotated[DecodeRequest, Body(openapi_examples=_DECODE_EXAMPLES)]) -> DecodeResponse:
    """Обратное к `encode`: по ключу восстанавливает id (разворот в фиксированной ширине обратим).

    Алгоритм: **LeetCode 7. Reverse Integer** → `algos.reverse_digits`. Бизнес-логика: `biz.infra.rowkeys`.
    """
    scheme = req.scheme.build()
    ids = []
    for k in req.keys:
        try:
            if scheme.storage != "string":
                if not (k.isascii() and k.isdigit()):  # int() принял бы и « 12 », и арабско-индийские цифры
                    raise ValueError(k)
                k = int(k)
            ids.append(str(decode(k, scheme)))
        except ValueError:
            ids.append(None)
    return DecodeResponse(ids=ids)


@router.post("/hotspot", summary="Нагрузка по регионам: прямой против развёрнутого", responses=_BAD_RANGE)
def hotspot_rowkeys(req: Annotated[HotspotRequest, Body(openapi_examples=_HOTSPOT_EXAMPLES)]) -> HotspotResponse:
    """Раскладывает пачку подряд идущих id `[start, start + count)` по регионам таблицы, заранее разбитой
    на `regions` равных отрезков пространства ключей, для прямого и развёрнутого ключа.

    Показывает и выигрыш (запись по всем регионам), и цену (чтение той же пачки обходит все регионы).
    Алгоритм: **LeetCode 7. Reverse Integer** → `algos.reverse_digits`. Бизнес-логика: `biz.infra.rowkeys`.
    """
    scheme = req.scheme.build()
    try:
        rep = compare_sequential(req.start, req.count, scheme, req.regions)
    except ValueError as e:  # в том числе KeyOverflow
        raise HTTPException(400, str(e)) from e
    return HotspotResponse(direct=_load(rep["direct"]), reversed=_load(rep["reversed"]))
