"""Демо: python -m biz.biotech.cloning.demo"""
import random
import time

from .analysis import check_primer, cloning_candidates, digest, find_sites
from .catalog import COMMON_ENZYMES as E


def random_dna(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("ACGT") for _ in range(n))


def main() -> None:
    rng = random.Random(5)

    # Вектор: 3 000 п.н. случайной ДНК + полилинкер (MCS) с сайтами 8 ферментов.
    mcs = "GAATTC" "GAGCTC" "GGTACC" "CCCGGG" "GGATCC" "TCTAGA" "GTCGAC" "AAGCTT"
    left, right = random_dna(rng, 1_500), random_dna(rng, 1_500)
    vector = left + mcs + right
    mcs_range = (len(left), len(left) + len(mcs))
    insert = random_dna(rng, 800)

    print(f"== Карта вектора ({len(vector)} п.н., кольцевой), только 6- и 8-щепящие")
    six = [e for e in E.values() if len(e.site) >= 6]
    sites = find_sites(vector, six, circular=True)
    for name, ss in sorted(sites.items(), key=lambda kv: (len(kv[1]), kv[0])):
        mark = "  ← в полилинкере" if len(ss) == 1 and mcs_range[0] <= ss[0].position < mcs_range[1] else ""
        print(f"  {name:<8} {E[name].pattern:<10} сайтов {len(ss)}: {[s.position for s in ss][:6]}{mark}")

    print("\n== Какие ферменты годятся для вставки (режут вектор один раз в MCS и не режут вставку)")
    for c in cloning_candidates(vector, insert, mcs_range, six):
        print(f"  {c.enzyme.name:<8} разрез на {c.cut}, концы {c.enzyme.ends.value:<5} {c.enzyme.overhang or '—'}")

    print("\n== Проверка клона: переваривание EcoRI + HindIII, длины фрагментов на геле")
    clone = left + mcs[:6] + insert + mcs[-6:] + right  # вставка между EcoRI и HindIII
    for name, seq in [("пустой вектор", vector), ("вектор со вставкой", clone)]:
        d = digest(seq, [E["EcoRI"], E["HindIII"]], circular=True)
        print(f"  {name:<19} разрезы {list(d.cuts)}  фрагменты {sorted(d.fragments, reverse=True)} п.н.")

    print("\n== Праймеры: самокомплементарность (self-dimer)")
    for primer in ["ATGACCATGATTACGCCAAG", "GTAAAACGACGGCCAGTGAATTC", "ATGCGAATTCGCAATTTGAC"]:
        r = check_primer(primer)
        stem = primer[r.stem[0]:r.stem[1]] if r.stem else "—"
        print(f"  {primer:<24} {r.verdict.value:<10} стебель {stem:<12} на 3'-конце {r.stem_3prime}")

    genome = random_dna(rng, 500_000)
    t0 = time.perf_counter()
    found = find_sites(genome, E.values())
    dt = time.perf_counter() - t0
    print(f"\n== Геном 500 000 п.н., весь каталог ({len(E)} ферментов): {sum(map(len, found.values()))} сайтов "
          f"за {dt:.2f} s")


if __name__ == "__main__":
    main()
