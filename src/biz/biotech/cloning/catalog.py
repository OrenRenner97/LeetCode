"""Часто используемые ферменты рестрикции II типа с палиндромными сайтами (данные REBASE).

^ — место разреза верхней цепи. SmaI и XmaI — изошизомеры: один сайт, разные места разреза.
"""
from .models import Enzyme

_PATTERNS = {
    # 6-щепящие: режут в среднем раз на 4⁶ = 4096 п.н., основа клонирования
    "EcoRI": "G^AATTC", "BamHI": "G^GATCC", "HindIII": "A^AGCTT", "XhoI": "C^TCGAG",
    "SalI": "G^TCGAC", "PstI": "CTGCA^G", "SmaI": "CCC^GGG", "XmaI": "C^CCGGG",
    "KpnI": "GGTAC^C", "SacI": "GAGCT^C", "XbaI": "T^CTAGA", "SpeI": "A^CTAGT",
    "NheI": "G^CTAGC", "NcoI": "C^CATGG", "NdeI": "CA^TATG", "EcoRV": "GAT^ATC",
    "BglII": "A^GATCT", "ApaI": "GGGCC^C", "MluI": "A^CGCGT", "ClaI": "AT^CGAT",
    # 8-щепящий: редкий (раз на 65 536 п.н.)
    "NotI": "GC^GGCCGC",
    # 4-щепящие: частые (раз на 256 п.н.), для «отпечатков» и проверки клонов
    "AluI": "AG^CT", "HaeIII": "GG^CC", "TaqI": "T^CGA", "MspI": "C^CGG", "DpnII": "^GATC",
}

COMMON_ENZYMES: dict[str, Enzyme] = {name: Enzyme.parse(name, p) for name, p in _PATTERNS.items()}
