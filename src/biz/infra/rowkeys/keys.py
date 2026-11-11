"""Ключ строки из последовательного id: прямой или «развёрнутый» (reverse the key).

Развёрнутый ключ = цифры id в обратном порядке в фиксированной ширине: id 1 000 000 123 при width 18 →
«000000001000000123» → «321000000100000000». Меняется быстрее всего младшая цифра id, а она теперь первая —
соседние id разлетаются по всему пространству ключей и по всем регионам.
"""
from dataclasses import dataclass

from algos.arithmetic import int_range, reverse_digits

# Тип колонки ключа → (bits, signed). string — строка из width цифр, лексикографический порядок = числовой.
STORAGES: dict[str, tuple[int, bool] | None] = {
    "int32": (32, True), "int64": (64, True), "uint64": (64, False), "string": None,
}
_STRING_DEFAULT_WIDTH = 20  # хватает на любой uint64


class KeyOverflow(ValueError):
    """Развёрнутый id не помещается в колонку ключа (как переполнение int32 в LeetCode 7)."""

    def __init__(self, id_: int, scheme: "KeyScheme"):
        super().__init__(f"id {id_}: развёрнутый ключ не помещается в {scheme.storage} при width = {scheme.width}. "
                         f"Безопасная ширина для {scheme.storage}: {max_safe_width(scheme.storage)}")
        self.id = id_


def max_safe_width(storage: str) -> int:
    """Наибольшая ширина, при которой любой развёрнутый id влезает в колонку: int32 → 9, int64 → 18, uint64 → 19.
    Для string ограничения нет: возвращается ширина по умолчанию (20)."""
    _check_storage(storage)
    if STORAGES[storage] is None:
        return _STRING_DEFAULT_WIDTH
    bits, signed = STORAGES[storage]
    hi = int_range(bits, signed=signed)[1]
    return len(str(hi + 1)) - 1  # 10^w − 1 ≤ hi ⟺ w < число цифр (hi + 1); hi + 1 — степень двойки, не 10^k


@dataclass(frozen=True)
class KeyScheme:
    """Как из id получается ключ.

    storage: тип колонки ключа ('int32' | 'int64' | 'uint64' | 'string').
    width: ширина в цифрах, id от 0 до 10^width − 1. По умолчанию — max_safe_width(storage).
        Больше безопасной можно (safe = False): тогда часть id не влезет — см. audit().
    reverse: True — развёрнутый ключ, False — прямой (сам id; для сравнения).
    """
    storage: str = "int64"
    width: int | None = None
    reverse: bool = True

    def __post_init__(self):
        _check_storage(self.storage)
        if self.width is None:
            object.__setattr__(self, "width", max_safe_width(self.storage))
        if not isinstance(self.width, int) or isinstance(self.width, bool) or self.width < 1:
            raise ValueError(f"width: ожидается целое >= 1, получено {self.width!r}")
        if not isinstance(self.reverse, bool):
            raise TypeError(f"reverse: ожидается bool, получено {type(self.reverse).__name__}")

    @property
    def max_id(self) -> int:
        return 10 ** self.width - 1

    @property
    def safe(self) -> bool:
        """Любой id из [0, max_id] даёт ключ, который влезает в колонку."""
        return self.width <= max_safe_width(self.storage)

    @property
    def key_space(self) -> int:
        """Ключи лежат в [0, key_space): по этому отрезку регионы и делятся заранее (pre-split)."""
        return 10 ** self.width


def encode(id_: int, scheme: KeyScheme) -> int | str:
    """Ключ строки для id. Для string — строка ровно из width цифр, иначе int.

    ValueError: id не int, отрицательный или больше scheme.max_id.
    KeyOverflow: ключ не помещается в колонку (только у схем с safe = False).
    """
    _check_id(id_, scheme)
    if scheme.storage == "string":
        key = reverse_digits(id_, width=scheme.width) if scheme.reverse else id_
        return str(key).zfill(scheme.width)
    bits, signed = STORAGES[scheme.storage]
    if not scheme.reverse:
        if id_ > int_range(bits, signed=signed)[1]:
            raise KeyOverflow(id_, scheme)
        return id_
    lo, hi = int_range(bits, signed=signed)
    if id_ > hi:  # id сам не влез в тип — тем более его ключ (у reverse_digits это ValueError про вход)
        raise KeyOverflow(id_, scheme)
    key = reverse_digits(id_, width=scheme.width, bits=bits, signed=signed)
    if key is None:
        raise KeyOverflow(id_, scheme)
    return key


def decode(key: int | str, scheme: KeyScheme) -> int:
    """id по ключу: decode(encode(i, s), s) == i. ValueError: ключ не той формы или вне [0, key_space)."""
    if scheme.storage == "string":
        if not isinstance(key, str) or len(key) != scheme.width or not key.isascii() or not key.isdigit():
            raise ValueError(f"ключ: ожидается строка из {scheme.width} цифр, получено {key!r}")
        key = int(key)
    elif not isinstance(key, int) or isinstance(key, bool):
        raise ValueError(f"ключ: ожидается int, получено {type(key).__name__}")
    if not 0 <= key < scheme.key_space:
        raise ValueError(f"ключ {key} вне [0, 10^{scheme.width})")
    return reverse_digits(key, width=scheme.width) if scheme.reverse else key


def audit(ids, scheme: KeyScheme) -> list[int]:
    """id, которые при этой схеме не получат ключ (переполнение колонки). Для safe-схем всегда пусто.

    Нужно перед миграцией: «можно ли взять width 19 под int64, раз наши id пока меньше 10^12?» — нельзя:
    первая цифра ключа = последняя цифра id, и id на …9 дают ключ ≥ 9·10^18 > 2^63 − 1.
    """
    bad = []
    for i in ids:
        try:
            encode(i, scheme)
        except KeyOverflow:
            bad.append(i)
    return bad


def _check_storage(storage) -> None:
    if storage not in STORAGES:
        raise ValueError(f"storage: ожидается одно из {tuple(STORAGES)}, получено {storage!r}")


def _check_id(id_, scheme: KeyScheme) -> None:
    if not isinstance(id_, int) or isinstance(id_, bool):
        raise ValueError(f"id: ожидается int, получено {type(id_).__name__}")
    if not 0 <= id_ <= scheme.max_id:
        raise ValueError(f"id {id_} вне [0, {scheme.max_id}] для width = {scheme.width}")
