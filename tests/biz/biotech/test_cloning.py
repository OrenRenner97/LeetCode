import random

import pytest

from biz.biotech.cloning import (
    COMMON_ENZYMES,
    Ends,
    Enzyme,
    PrimerVerdict,
    check_primer,
    cloning_candidates,
    digest,
    find_sites,
    reverse_complement,
)

E = COMMON_ENZYMES


def _naive_sites(seq, enzymes, circular):
    # Эталон: str.find по каждому ферменту.
    n = len(seq)
    out = {}
    for e in enzymes:
        scan = seq + (seq * len(e.site))[: len(e.site) - 1] if circular and n else seq
        pos, found = scan.find(e.site), []
        while pos != -1 and pos < n:
            found.append(pos)
            pos = scan.find(e.site, pos + 1)
        out[e.name] = found
    return out


def test_catalog_is_consistent():
    for e in E.values():
        assert e.site == reverse_complement(e.site)
    assert (E["EcoRI"].ends, E["EcoRI"].overhang) == (Ends.FIVE_PRIME, "AATT")
    assert (E["PstI"].ends, E["PstI"].overhang) == (Ends.THREE_PRIME, "TGCA")
    assert (E["EcoRV"].ends, E["EcoRV"].overhang) == (Ends.BLUNT, "")
    assert E["BamHI"].overhang == E["BglII"].overhang == E["DpnII"].overhang == "GATC"  # совместимые концы
    assert E["SmaI"].site == E["XmaI"].site and E["SmaI"].ends != E["XmaI"].ends     # изошизомеры


def test_enzyme_validation():
    with pytest.raises(ValueError):
        Enzyme.parse("bad", "GAATTC")       # нет '^'
    with pytest.raises(ValueError):
        Enzyme.parse("BsaI", "GGTCTC^")     # не палиндром (IIS) — не поддерживаем
    with pytest.raises(ValueError):
        Enzyme.parse("odd", "GA^NTC")       # вырожденный сайт
    with pytest.raises(ValueError):
        Enzyme("x", "GAATTC", 7)


def test_find_sites_basic():
    seq = "ttGAATTCaaGGATCCgaattc"
    sites = find_sites(seq, [E["EcoRI"], E["BamHI"], E["NotI"]])
    assert [(s.position, s.cut) for s in sites["EcoRI"]] == [(2, 3), (16, 17)]
    assert [(s.position, s.cut) for s in sites["BamHI"]] == [(10, 11)]
    assert sites["NotI"] == []


def test_isoschizomers_and_nested_sites():
    # CCCGGG — SmaI и XmaI; внутри него CCGG — MspI. Один палиндромный центр — три фермента.
    sites = find_sites("aaCCCGGGtt", [E["SmaI"], E["XmaI"], E["MspI"]])
    assert [(s.position, s.cut) for s in sites["SmaI"]] == [(2, 5)]
    assert [(s.position, s.cut) for s in sites["XmaI"]] == [(2, 3)]
    assert [(s.position, s.cut) for s in sites["MspI"]] == [(3, 4)]


def test_circular_site_across_origin():
    seq = "ATTCaaaaaaaaGA"  # GA|ATTC через стык кольца
    assert find_sites(seq, [E["EcoRI"]])["EcoRI"] == []
    (site,) = find_sites(seq, [E["EcoRI"]], circular=True)["EcoRI"]
    assert (site.position, site.cut) == (12, 13)


def test_random_against_naive():
    rng = random.Random(3)
    enzymes = list(E.values())
    for _ in range(150):
        seq = "".join(rng.choice("ACGT" * 5 + "N") for _ in range(rng.randint(0, 400)))
        for circular in (False, True):
            got = {k: [s.position for s in v] for k, v in find_sites(seq, enzymes, circular=circular).items()}
            assert got == _naive_sites(seq, enzymes, circular), (seq, circular)


def test_digest_linear_and_circular():
    seq = "aaaaGAATTCaaaaaaaaaaGGATCCaaaa"  # 30 п.н., разрезы после 5 и 21
    assert digest(seq, [E["EcoRI"], E["BamHI"]]).fragments == (5, 16, 9)
    circ = digest(seq, [E["EcoRI"], E["BamHI"]], circular=True)
    assert circ.cuts == (5, 21) and circ.fragments == (16, 14)
    assert digest(seq, [E["NotI"]], circular=True).fragments == (30,)  # кольцо не разрезано
    assert digest("GATCaaaa", [E["DpnII"]]).fragments == (8,)           # разрез на самом краю — не разрез


def test_cloning_candidates():
    rng = random.Random(1)
    backbone = "".join(rng.choice("AT") for _ in range(300))  # только A/T: 6-щепящих сайтов нет
    mcs = "GAATTCGGATCCAAGCTTCTCGAG"                         # EcoRI, BamHI, HindIII, XhoI
    vector = backbone[:100] + mcs + backbone[100:] + "GAATTC"  # второй EcoRI вне полилинкера
    insert = "ATGGCC" + "GGATCC" + "TTTAAA"                   # во вставке есть BamHI
    got = cloning_candidates(vector, insert, (100, 100 + len(mcs)),
                             [E["EcoRI"], E["BamHI"], E["HindIII"], E["XhoI"], E["NotI"]])
    assert [c.enzyme.name for c in got] == ["HindIII", "XhoI"]
    assert [c.cut for c in got] == [113, 119]
    with pytest.raises(ValueError):
        cloning_candidates(vector, insert, (10, 5))


@pytest.mark.parametrize(
    "primer, verdict, stem, at3",
    [
        ("ATGCTAGCTTGACAGTCAGT", PrimerVerdict.OK, (2, 8), 0),          # GCTAGC — 6, на пределе
        ("ATGCGAATTCGCAATTTGAC", PrimerVerdict.SELF_DIMER, (1, 13), 0),  # TGCGAATTCGCA — 12
        ("TTGACAGTCATGGATCC", PrimerVerdict.SELF_DIMER, (11, 17), 6),    # GGATCC на 3'-конце
        ("acgtnACGT", PrimerVerdict.HAS_N, None, 0),
    ],
)
def test_check_primer(primer, verdict, stem, at3):
    r = check_primer(primer)
    assert (r.verdict, r.stem, r.stem_3prime) == (verdict, stem, at3)


def test_input_validation():
    with pytest.raises(ValueError):
        find_sites("GAATTX")
    with pytest.raises(ValueError):
        find_sites("GAATTC", [E["EcoRI"], E["EcoRI"]])
    assert find_sites("gaat tc\nGAATTC", [E["EcoRI"]])["EcoRI"][1].position == 6  # регистр и пробелы — ок
