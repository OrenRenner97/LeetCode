import random

import pytest

from biz.edtech.railfence import Key, crack, decrypt, detect_language, encrypt, grid, group, letters_only, score

# Тексты не из корпуса модели языка: иначе взлом проверялся бы на обучающих данных.
EN = "Meet me at the north gate of the park at nine and bring the map and a flashlight"
RU = "Встречаемся у северного входа в парк ровно в девять, захвати карту и фонарик"


def test_classic_example():
    # Классический пример из учебников и LeetCode 6.
    assert encrypt("WEAREDISCOVEREDFLEEATONCE", Key(3)) == "WECRLTEERDSOEEFEAOCAIVDEN"
    assert encrypt("PAYPALISHIRING", Key(4)) == "PINALSIGYAHRPI"
    assert grid("WEAREDISCOVERED", Key(3)) == ["W...E...C...R..", ".E.R.D.S.O.E.E.", "..A...I...V...D"]


def test_offset_example():
    # Сдвиг 2 при 3 строках: зигзаг начинается с нижней строки и идёт вверх.
    assert grid("ABCDE", Key(3, 2)) == ["..C..", ".B.D.", "A...E"]
    assert encrypt("ABCDE", Key(3, 2)) == "CBDAE"
    assert decrypt("CBDAE", Key(3, 2)) == "ABCDE"


def test_roundtrip_random():
    rng = random.Random(6)
    for _ in range(2000):
        text = "".join(rng.choice("abc XYZ,.") for _ in range(rng.randint(0, 40)))
        rails = rng.randint(1, 15)
        key = Key(rails, rng.randrange(max(2 * (rails - 1), 1)))
        enc = encrypt(text, key)
        assert sorted(enc) == sorted(text)
        assert decrypt(enc, key) == text, (text, key)
        assert "".join(line.replace(".", "") for line in grid(text, key)) == enc or "." in text


def test_grid_reads_as_ciphertext():
    rng = random.Random(1)
    for _ in range(300):
        text = "".join(rng.choice("ABCDEFG") for _ in range(rng.randint(1, 30)))
        rails = rng.randint(1, 8)
        key = Key(rails, rng.randrange(max(2 * (rails - 1), 1)))
        assert "".join(line.replace(".", "") for line in grid(text, key)) == encrypt(text, key)


@pytest.mark.parametrize("plain, key", [
    (EN, Key(3)), (EN, Key(5, 3)), (letters_only(EN), Key(7, 10)),
    (RU, Key(4)), (RU, Key(6, 7)), (letters_only(RU), Key(9, 2)),
])
def test_crack_recovers(plain, key):
    res = crack(encrypt(plain, key))
    assert res.best.plaintext == plain or any(c.plaintext == plain for c in res.rotations)
    assert res.language == ("ru" if plain in (RU, letters_only(RU)) else "en")


def test_crack_confident_and_correct_on_long_text():
    plain = EN + ". " + EN.replace("nine", "ten").replace("map", "radio")
    res = crack(encrypt(plain, Key(6, 4)))
    assert res.confident and res.best.plaintext == plain


def test_short_text_is_not_confident():
    res = crack(encrypt("HELLO WORLD", Key(3)))
    assert not res.confident


def test_rotations_reported():
    # Сдвиг даёт поворот текста: шифротекст одинаково объясняется обоими, взлом обязан это сказать.
    plain = letters_only(EN)
    res = crack(encrypt(plain, Key(5, 3)))
    found = [res.best, *res.rotations]
    assert any(c.plaintext == plain for c in found)
    for c in res.rotations:
        assert c.plaintext in res.best.plaintext * 2 and c.plaintext != res.best.plaintext


def test_crack_dedupes_and_counts_keys():
    res = crack("ABCD", max_rails=40, top=100)
    # rails ≤ n = 4: 2 + 4 + 6 = 12 ключей, расшифровок меньше (часть совпадает)
    assert res.keys_tried == 12
    assert len({c.plaintext for c in res.candidates}) == len(res.candidates)


def test_score_separates_text_from_shuffle():
    # Настоящий текст > 0, любая из 200 перестановок его букв < 0 (замер: 0.30 против максимум −0.27
    # для английского, 0.19 против −0.17 для русского; медиана перестановок −0.68 / −0.51).
    for text, lang in ((EN, "en"), (RU, "ru")):
        assert score(text, lang) > 0.1
        for seed in range(200):
            letters = list(letters_only(text))
            random.Random(seed).shuffle(letters)
            assert score("".join(letters), lang) < 0, seed


def test_detect_language_and_helpers():
    assert detect_language(RU) == "ru" and detect_language(EN) == "en"
    assert letters_only("Ёлка, ok!") == "ЕЛКАOK"
    assert group("WECRERDSOEEAIVD") == "WECRE RDSOE EAIVD"


def test_validation():
    for bad in (dict(rails=0), dict(rails=3, offset=4), dict(rails=3, offset=-1), dict(rails=1, offset=1)):
        with pytest.raises(ValueError):
            Key(**bad)
    for bad in (dict(rails=2.0), dict(rails=True), dict(rails=3, offset="1")):
        with pytest.raises(TypeError):
            Key(**bad)
    with pytest.raises(ValueError):
        crack("abc", language="de")
    with pytest.raises(ValueError):
        crack("abc", max_rails=1)
    with pytest.raises(ValueError):
        group("abc", 0)
