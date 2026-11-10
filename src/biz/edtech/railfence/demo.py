"""Демо: python -m biz.edtech.railfence.demo"""
import time

from .cipher import decrypt, encrypt, grid, group, letters_only
from .crack import crack
from .models import Key


def main() -> None:
    print("== Как устроен шифр (это и есть LeetCode 6. Zigzag Conversion)")
    text, key = "WEAREDISCOVERED", Key(3)
    for line in grid(text, key):
        print("  ", line)
    print(f"  читаем строки подряд → {encrypt(text, key)}")

    print("\n== Сдвиг начала зигзага: тот же текст, Key(3, offset=2)")
    for line in grid(text, Key(3, 2)):
        print("  ", line)
    print(f"  → {encrypt(text, Key(3, 2))}")

    print("\n== Задание для CTF: текст без пробелов, блоками по 5")
    secret = "The archive key is hidden under the third step of the lighthouse stairs"
    task = group(encrypt(letters_only(secret), Key(7, 5)))
    print(f"  шифротекст: {task}")

    print("\n== Взлом без ключа")
    t = time.perf_counter()
    res = crack(task.replace(" ", ""))
    took = (time.perf_counter() - t) * 1e3
    print(f"  перебрано ключей: {res.keys_tried} за {took:.0f} ms, язык {res.language}, уверен: {res.confident}")
    for c in res.candidates[:3]:
        print(f"  {c.score:+.2f}  rails={c.key.rails:<2} offset={c.key.offset:<2} {c.plaintext}")
    if res.rotations:
        print(f"  повороты лучшего (тот же шифротекст, выбрать может только человек): {len(res.rotations)}")
    assert decrypt(task.replace(" ", ""), Key(7, 5)) == letters_only(secret)

    print("\n== Короткий текст: статистики мало — взлом честно не уверен")
    res = crack(encrypt("ПРИВЕТ МИР", Key(3)))
    print(f"  уверен: {res.confident}; лучшие: {[c.plaintext for c in res.candidates[:3]]}")


if __name__ == "__main__":
    main()
