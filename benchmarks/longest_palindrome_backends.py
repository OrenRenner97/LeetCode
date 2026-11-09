"""Шаг 3 для задачи 5.   uv run benchmarks/longest_palindrome_backends.py

1. palindrome_radii по backend'ам: короткие строки (праймеры) → геномы; обычная строка, "aaa…", ДНК с комплементом.
2. Где уходит время: кодирование входа, ядро, list(radii), разбор в Python.
3. Бизнес целиком: find_sites (геном, весь каталог) и check_primer (20 п.н.) по backend'ам.
"""
import random
import string
import time
from functools import partial

import numpy as np
from bench import bench

from algos._native import c_impl, numba_impl
from algos._native.mirror_codes import encode
from algos.palindromes import longest_palindrome, maximal_palindromes, palindrome_radii
from biz.biotech.cloning import COMMON_ENZYMES, check_primer, find_sites
from biz.biotech.cloning.models import COMPLEMENT


def by_backend(fn, **kw):
    return {b: partial(fn, backend=b, **kw) for b in palindrome_radii.backends}


def text(kind):
    def make(n):
        rng = random.Random(n)
        if kind == "letters":
            return ("".join(rng.choice(string.ascii_letters) for _ in range(n)),)
        if kind == "same":
            return ("a" * n,)
        return ("".join(rng.choice("ACGT") for _ in range(n)),)
    return make


def t(fn, *a, repeat=5, **kw):
    fn(*a, **kw)
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*a, **kw)
        best = min(best, time.perf_counter() - t0)
    return best


def fmt(sec):
    return f"{sec * 1e6:9.1f} µs" if sec < 1e-3 else f"{sec * 1e3:9.2f} ms"


if __name__ == "__main__":
    sizes = [20, 200, 2_000, 100_000, 1_000_000]
    print("################ 1. palindrome_radii ################")
    for kind, kw in [("letters", {}), ("same", {}), ("dna", {"mirror": COMPLEMENT})]:
        print(f"\n======== {kind} {'+ mirror' if kw else ''}", end="")
        bench(by_backend(palindrome_radii, **kw), text(kind), sizes, repeat=3, warmup=1)

    print("\n################ 2. Из чего складывается вызов (ДНК 10⁶ + mirror) ################")
    (dna,) = text("dna")(1_000_000)
    a, b, um = encode(dna, COMPLEMENT)
    out = np.empty(2 * a.shape[0] + 1, np.int64)
    radii = numba_impl.palindrome_radii_numba(dna, COMPLEMENT)
    rows = {
        "encode (UTF-32 + таблица комплемента)": t(encode, dna, COMPLEMENT),
        "ядро numba": t(numba_impl._palindrome_radii, a, b, um, out),
        "ядро C (через c_impl, с encode)": t(c_impl.palindrome_radii_c, dna, COMPLEMENT),
        "radii.tolist()": t(radii.tolist),
        "maximal_palindromes(min 4), numba": t(maximal_palindromes, dna, min_length=4, mirror=COMPLEMENT,
                                                backend="numba"),
        "longest_palindrome, numba": t(longest_palindrome, dna, mirror=COMPLEMENT, backend="numba"),
        "старый find_sites: цикл Python по 2·10⁶ радиусам": t(lambda r: [x for x in r[::2] if x >= 4],
                                                              radii.tolist()),
    }
    for name, sec in rows.items():
        print(f"  {name:<52}{fmt(sec)}")

    print("\n################ 3. Бизнес целиком ################")
    for n in [10_000, 1_000_000]:
        (genome,) = text("dna")(n)
        line = "  ".join(f"{b} {fmt(t(find_sites, genome, COMMON_ENZYMES.values(), backend=b, repeat=3))}"
                         for b in palindrome_radii.backends)
        print(f"  find_sites, геном {n:>9,} п.н., 26 ферментов:  {line}")
    primer = "GTAAAACGACGGCCAGTGAATTC"
    line = "  ".join(f"{b} {fmt(t(check_primer, primer, backend=b, repeat=200))}" for b in palindrome_radii.backends)
    print(f"  check_primer, {len(primer)} п.н.:  {line}")
