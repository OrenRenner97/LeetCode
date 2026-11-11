"""Демо: python -m biz.infra.rowkeys.demo"""
from algos import reverse_digits

from .hotspot import compare_sequential
from .keys import KeyOverflow, KeyScheme, audit, decode, encode, max_safe_width


def _bar(loads):
    top = max(loads)
    return " ".join(f"{x * 9 // top}" if top else "0" for x in loads)


def main() -> None:
    print("== Заказы получают id подряд: 1000000001, 1000000002, …")
    scheme = KeyScheme("int64")  # width 18 — безопасная для int64
    for i in (1_000_000_001, 1_000_000_002, 1_000_000_003):
        print(f"  id {i} → прямой ключ {i:>18} | развёрнутый {encode(i, scheme)}")

    print("\n== Куда пишут 100 000 новых заказов (таблица заранее разбита на 16 регионов)")
    rep = compare_sequential(1_000_000_000, 100_000, scheme, 16)
    for name, r in rep.items():
        print(f"  {name:<8} нагрузка по регионам (шкала 0–9): {_bar(r.loads)}  "
              f"самый горячий регион: {r.hottest_share:.0%}, регионов задействовано: {r.regions_touched}")
    print("  обратная сторона: «последние 100 000 заказов» по развёрнутому ключу — запрос во все 16 регионов")

    print("\n== Почему нужна фиксированная ширина: без неё разворот не обратим")
    print(f"  reverse(12) = {reverse_digits(12)}, reverse(120) = {reverse_digits(120)}, "
          f"reverse(1200) = {reverse_digits(1200)} — три заказа в одну строку")
    s4 = KeyScheme("string", 4)
    print(f"  width 4: {[encode(i, s4) for i in (12, 120, 1200)]} — разные; decode обратно: "
          f"{[decode(encode(i, s4), s4) for i in (12, 120, 1200)]}")

    print("\n== Переполнение (ровно LeetCode 7): хочется width 19, «ведь id в int64 влезают»")
    print(f"  безопасная ширина: int32 → {max_safe_width('int32')}, int64 → {max_safe_width('int64')}, "
          f"uint64 → {max_safe_width('uint64')}")
    s19 = KeyScheme("int64", 19)
    ids = range(10**9, 10**9 + 100_000)
    bad = audit(ids, s19)
    print(f"  width 19 под int64: safe = {s19.safe}; из {len(ids)} реальных id не влезут {len(bad)} "
          f"({len(bad) / len(ids):.1%})")
    try:
        encode(1_000_000_099, s19)  # ключ 9 900 000 000 100 000 000 > 2^63 − 1
    except KeyOverflow as e:
        print(f"  {e}")


if __name__ == "__main__":
    main()
