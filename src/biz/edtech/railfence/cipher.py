"""Шифр «изгородь» (rail fence): ровно LeetCode 6. Zigzag Conversion, плюс сдвиг начала и расшифровка."""
from algos.permutations import zigzag_decode, zigzag_encode, zigzag_rows

from .models import Key

_PAD = object()


def encrypt(plaintext: str, key: Key, *, backend: str | None = None) -> str:
    """Зигзаг по key.rails строкам, начиная с фазы key.offset, затем чтение построчно.

    encrypt("WEAREDISCOVERED", Key(3)) == "WECRERDSOEEAIVD". Шифруются все символы, включая пробелы
    и знаки: так принято в задачах на этот шифр. Нужен только алфавит — сначала letters_only().
    """
    if key.offset == 0:
        return zigzag_encode(plaintext, key.rails, backend=backend)
    # Сдвиг = будто перед текстом уже стоят offset символов: дописываем пустышки и выбрасываем их.
    padded = [_PAD] * key.offset + list(plaintext)
    return "".join(x for x in zigzag_encode(padded, key.rails, backend=backend) if x is not _PAD)


def decrypt(ciphertext: str, key: Key, *, backend: str | None = None) -> str:
    """Обратное к encrypt: decrypt(encrypt(t, k), k) == t."""
    if key.offset == 0:
        return zigzag_decode(ciphertext, key.rails, backend=backend)
    n = len(ciphertext)
    # Куда в зашифрованном тексте попали бы пустышки: шифруем маску «пустышка / символ».
    mask = zigzag_encode([True] * key.offset + [False] * n, key.rails, backend=backend)
    chars = iter(ciphertext)
    padded = [_PAD if is_pad else next(chars) for is_pad in mask]
    return "".join(zigzag_decode(padded, key.rails, backend=backend)[key.offset:])


def grid(text: str, key: Key, *, blank: str = ".") -> list[str]:
    """Картинка зигзага для объяснения: key.rails строк, символ текста в своей строке, остальное — blank.

    grid("WEAREDISCOVERED", Key(3)) == ["W...E...C...R..", ".E.R.D.S.O.E.E.", "..A...I...V...D"].
    Прочитать строки подряд, выбросив blank, — это и есть шифротекст.
    """
    lines = [[blank] * len(text) for _ in range(key.rails)]
    for pos, (row, ch) in enumerate(zip(zigzag_rows(key.offset + len(text), key.rails)[key.offset:], text)):
        lines[row][pos] = ch
    return ["".join(line) for line in lines]


def letters_only(text: str) -> str:
    """Классическая подготовка текста: только буквы, верхний регистр, Ё → Е."""
    return "".join(ch for ch in text.upper().replace("Ё", "Е") if ch.isalpha())


def group(text: str, size: int = 5) -> str:
    """Блоки по size символов через пробел — так шифротекст не выдаёт длину слов: 'WECRE RDSOE EAIVD'."""
    if size < 1:
        raise ValueError(f"size должен быть >= 1, получено {size}")
    return " ".join(text[i:i + size] for i in range(0, len(text), size))
