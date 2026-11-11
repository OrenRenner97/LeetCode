"""Нагрузка по регионам: куда попадут записи пачки id при заданной схеме ключей.

Регионы (HBase region, Bigtable tablet, диапазон шарда) — непрерывные отрезки пространства ключей.
Считаем, что таблица заранее разбита (pre-split) на `regions` равных отрезков [0, key_space).
"""
from dataclasses import dataclass

from .keys import KeyScheme, encode


@dataclass(frozen=True)
class LoadReport:
    loads: tuple[int, ...]      # сколько id попало в каждый регион
    total: int
    regions_touched: int        # в скольких регионах есть записи

    @property
    def hottest_share(self) -> float:
        """Доля самого нагруженного региона: 1.0 — всё в одном (hotspot), 1/regions — идеально ровно."""
        return max(self.loads) / self.total if self.total else 0.0

    @property
    def skew(self) -> float:
        """Максимум / среднее: 1.0 — ровно, regions — всё в одном регионе."""
        return max(self.loads) * len(self.loads) / self.total if self.total else 0.0


def region_of(key: int | str, scheme: KeyScheme, regions: int) -> int:
    k = int(key) if isinstance(key, str) else key
    return k * regions // scheme.key_space


def region_loads(ids, scheme: KeyScheme, regions: int) -> LoadReport:
    """Раскладывает ids по регионам. ValueError: regions < 1; ошибки encode() пробрасываются.

    regions_touched читается двояко: при записи — сколько регионов делят нагрузку, при чтении этой же пачки
    (например, «последние N заказов») — во сколько регионов уйдёт запрос. Развёрнутый ключ улучшает первое
    и ухудшает второе: это цена приёма.
    """
    if not isinstance(regions, int) or isinstance(regions, bool) or regions < 1:
        raise ValueError(f"regions: ожидается целое >= 1, получено {regions!r}")
    loads = [0] * regions
    for i in ids:
        loads[region_of(encode(i, scheme), scheme, regions)] += 1
    total = sum(loads)
    return LoadReport(tuple(loads), total, sum(1 for x in loads if x))


def compare_sequential(start: int, count: int, scheme: KeyScheme, regions: int) -> dict[str, LoadReport]:
    """Пачка подряд идущих id [start, start + count) при прямом и развёрнутом ключе той же ширины и колонки:
    {'direct': ..., 'reversed': ...}. ValueError: count < 1."""
    if not isinstance(count, int) or count < 1:
        raise ValueError(f"count: ожидается целое >= 1, получено {count!r}")
    ids = range(start, start + count)
    direct = KeyScheme(scheme.storage, scheme.width, reverse=False)
    rev = KeyScheme(scheme.storage, scheme.width, reverse=True)
    return {"direct": region_loads(ids, direct, regions), "reversed": region_loads(ids, rev, regions)}
