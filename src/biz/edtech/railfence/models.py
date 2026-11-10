from dataclasses import dataclass


@dataclass(frozen=True)
class Key:
    """Ключ шифра «изгородь»: число строк (rails) и сдвиг начала зигзага (offset).

    offset = 0 — классика (LeetCode 6): первый символ в верхней строке, дальше вниз.
    offset = k — зигзаг начинается так, будто k символов уже записаны: первый символ стоит в строке,
    куда попал бы (k + 1)-й. Сдвиги различаются только по модулю периода 2·(rails - 1),
    поэтому допустимы 0 <= offset < period. С одной строкой шифр тождественный, offset = 0.
    """
    rails: int
    offset: int = 0

    def __post_init__(self):
        for name in ("rails", "offset"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} должен быть int, получено {type(value).__name__}")
        if self.rails < 1:
            raise ValueError(f"rails должен быть >= 1, получено {self.rails}")
        if not 0 <= self.offset < max(self.period, 1):
            raise ValueError(f"offset должен быть в [0, {max(self.period, 1)}) для rails = {self.rails}, "
                             f"получено {self.offset}")

    @property
    def period(self) -> int:
        """Через сколько символов зигзаг повторяется: вниз rails - 1 шагов и вверх rails - 1."""
        return 2 * (self.rails - 1)


@dataclass(frozen=True)
class Candidate:
    key: Key
    plaintext: str
    score: float  # средний вклад пары букв: > 0 похоже на язык, < 0 похоже на перемешанные буквы


@dataclass(frozen=True)
class CrackResult:
    """Кандидаты по убыванию score (одинаковые расшифровки схлопнуты, остаётся наименьший ключ).

    confident — текста достаточно для статистики и лучший кандидат заметно лучше всех, кто не является
    его циклическим поворотом. Если False, ответ стоит проверить глазами среди первых кандидатов.

    rotations — циклические повороты лучшей расшифровки, которые дают другие сдвиги того же числа строк.
    Это свойство шифра со сдвигом: шифротекст одинаково хорошо объясняется текстом и его поворотом,
    а биграммы у них отличаются одной парой на стыке. Выбрать между ними может только человек
    (обычно видно по обрезанному слову в начале).
    """
    language: str
    candidates: tuple[Candidate, ...]
    keys_tried: int
    confident: bool
    rotations: tuple[Candidate, ...] = ()

    @property
    def best(self) -> Candidate | None:
        return self.candidates[0] if self.candidates else None
