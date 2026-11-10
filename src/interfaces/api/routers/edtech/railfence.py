from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, model_validator

from biz.edtech.railfence import Key, crack, decrypt, encrypt, grid, group, letters_only

from ...errors import BAD_BACKEND
from ...schemas import Backend

router = APIRouter(prefix="/railfence", tags=["edtech/railfence"])


class KeyIn(BaseModel):
    rails: int = Field(ge=1, le=10_000, description="Число строк зигзага (ключ шифра)")
    offset: int = Field(0, ge=0, description="Сдвиг начала зигзага: 0 ≤ offset < 2·(rails − 1). "
                                             "0 — классика, первый символ в верхней строке")

    @model_validator(mode="after")
    def _valid(self):
        Key(self.rails, self.offset)  # ValueError → 422 с объяснением
        return self


class EncryptRequest(BaseModel):
    text: str = Field(max_length=100_000, description="Открытый текст. Шифруются все символы, включая пробелы")
    key: KeyIn = Field(description="Ключ")
    letters_only: bool = Field(False, description="Сначала оставить только буквы в верхнем регистре (Ё → Е), "
                                                 "как принято в классических заданиях")
    group_by: int | None = Field(None, ge=1, le=100, description="Разбить шифротекст на блоки этой длины через "
                                                                  "пробел (обычно 5), чтобы не выдавать длину слов")
    with_grid: bool = Field(False, description="Вернуть картинку зигзага (только для текста до 500 символов)")
    backend: Backend = None


class EncryptResponse(BaseModel):
    ciphertext: str = Field(description="Шифротекст")
    grid: list[str] | None = Field(description="Строки зигзага, пустые клетки — точки. Прочитать подряд без точек "
                                               "= шифротекст. `null`, если не запрошено")


class DecryptRequest(BaseModel):
    ciphertext: str = Field(max_length=100_000, description="Шифротекст ровно в том виде, в каком шифровали "
                                                            "(пробелы группировки убрать заранее)")
    key: KeyIn = Field(description="Ключ")
    backend: Backend = None


class DecryptResponse(BaseModel):
    plaintext: str = Field(description="Открытый текст")


class CrackRequest(BaseModel):
    ciphertext: str = Field(min_length=1, max_length=2_000,
                            description="Шифротекст до 2000 символов: перебор ~max_rails² ключей, ~0.1 s на 60 букв "
                                        "и ~1.8 s на 5000")
    language: Literal["auto", "en", "ru"] = Field("auto", description="Язык открытого текста; `auto` — по алфавиту")
    max_rails: int = Field(40, ge=2, le=60, description="Перебирать ключи с числом строк до этого")
    top: int = Field(5, ge=1, le=50, description="Сколько лучших расшифровок вернуть")
    backend: Backend = None


class CandidateOut(BaseModel):
    rails: int = Field(description="Число строк")
    offset: int = Field(description="Сдвиг начала зигзага")
    plaintext: str = Field(description="Расшифровка этим ключом")
    score: float = Field(description="Похожесть на язык: средний вклад пары букв. > 0 — похоже на текст, "
                                     "< 0 — на перемешанные буквы")


class CrackResponse(BaseModel):
    language: Literal["en", "ru"] = Field(description="Язык, по которому оценивали")
    keys_tried: int = Field(description="Сколько ключей перебрано")
    confident: bool = Field(description="Лучший кандидат заметно лучше всех, кроме своих поворотов, и текста "
                                        "достаточно (от 40 букв). Иначе проверить глазами")
    candidates: list[CandidateOut] = Field(description="Лучшие расшифровки по убыванию score, без повторов")
    rotations: list[CandidateOut] = Field(
        description="Циклические повороты лучшей расшифровки от других сдвигов. Шифротекст объясняется ими "
                    "одинаково хорошо, статистика их не различает — выбрать по смыслу (обрезанное слово в начале)")


def _out(c) -> CandidateOut:
    return CandidateOut(rails=c.key.rails, offset=c.key.offset, plaintext=c.plaintext, score=round(c.score, 4))


_ENCRYPT_EXAMPLES = {
    "classic": {
        "summary": "Классика: 3 строки, с картинкой",
        "description": "Тот самый пример из условия LeetCode 6.",
        "value": {"text": "WEAREDISCOVERED", "key": {"rails": 3}, "with_grid": True},
    },
    "ctf": {
        "summary": "Задание для CTF: только буквы, блоки по 5, сдвиг",
        "value": {"text": "The archive key is hidden under the third step", "key": {"rails": 5, "offset": 3},
                  "letters_only": True, "group_by": 5},
    },
}
_DECRYPT_EXAMPLES = {
    "classic": {"summary": "Расшифровать классический пример",
                "value": {"ciphertext": "WECRERDSOEEAIVD", "key": {"rails": 3}}},
}
_CRACK_EXAMPLES = {
    "en": {
        "summary": "Взлом английского текста без ключа",
        "description": "Ключ (7, 5). Лучший кандидат и его повороты — среди них настоящий текст.",
        "value": {"ciphertext": "IEILAHVDNHREITICEDUTDHGSRRKINESTHESAEHDHTFTSTEYSETEOHUHIRPO"},
    },
    "ru": {
        "summary": "Взлом русского текста с пробелами",
        "description": "Ключ (4, 0): пробелы и знаки тоже переставлены.",
        "value": {"ciphertext": "Ваурвв  яа сче  ен х  кроввтзхикутемясвоооапрон еь втатрсегдавд,ар",
                  "language": "ru"},
    },
}


@router.post("/encrypt", summary="Зашифровать «изгородью»", responses=BAD_BACKEND)
def encrypt_railfence(req: Annotated[EncryptRequest, Body(openapi_examples=_ENCRYPT_EXAMPLES)]) -> EncryptResponse:
    """Пишет текст зигзагом по `rails` строкам (с фазы `offset`) и читает построчно.

    Это ровно **LeetCode 6. Zigzag Conversion** → `algos.zigzag_encode`. Картинка зигзага (`with_grid`)
    нужна для объяснения в задании. Бизнес-логика: `biz.edtech.railfence`.
    """
    key = Key(req.key.rails, req.key.offset)
    text = letters_only(req.text) if req.letters_only else req.text
    cipher = encrypt(text, key, backend=req.backend)
    return EncryptResponse(ciphertext=group(cipher, req.group_by) if req.group_by else cipher,
                           grid=grid(text, key) if req.with_grid and len(text) <= 500 else None)


@router.post("/decrypt", summary="Расшифровать по ключу", responses=BAD_BACKEND)
def decrypt_railfence(req: Annotated[DecryptRequest, Body(openapi_examples=_DECRYPT_EXAMPLES)]) -> DecryptResponse:
    """Обратная перестановка: раскладывает шифротекст обратно по строкам зигзага.

    `algos.zigzag_decode` (обратная к **LeetCode 6. Zigzag Conversion**). Бизнес-логика: `biz.edtech.railfence`.
    """
    return DecryptResponse(plaintext=decrypt(req.ciphertext, Key(req.key.rails, req.key.offset), backend=req.backend))


@router.post("/crack", summary="Взломать без ключа", responses=BAD_BACKEND)
def crack_railfence(req: Annotated[CrackRequest, Body(openapi_examples=_CRACK_EXAMPLES)]) -> CrackResponse:
    """Перебирает все ключи `(rails, offset)` до `max_rails` и ранжирует расшифровки по частотам пар букв
    языка (перестановка не меняет состав букв, поэтому различает кандидатов только порядок).

    Честно сообщает, когда не уверен: на коротком тексте и когда другой сдвиг даёт циклический поворот
    того же текста (`rotations`). Алгоритм: **LeetCode 6. Zigzag Conversion** → `algos.zigzag_decode`.
    Бизнес-логика: `biz.edtech.railfence`.
    """
    res = crack(req.ciphertext, language=req.language, max_rails=req.max_rails, top=req.top, backend=req.backend)
    return CrackResponse(language=res.language, keys_tried=res.keys_tried, confident=res.confident,
                         candidates=[_out(c) for c in res.candidates], rotations=[_out(c) for c in res.rotations])
