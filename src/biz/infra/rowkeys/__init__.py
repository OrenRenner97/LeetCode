"""Ключи строк из последовательных id: прямые и развёрнутые (anti-hotspot). Алгоритм: algos.reverse_digits (LeetCode 7)."""
from .hotspot import LoadReport, compare_sequential, region_loads, region_of
from .keys import STORAGES, KeyOverflow, KeyScheme, audit, decode, encode, max_safe_width

__all__ = ["STORAGES", "KeyOverflow", "KeyScheme", "LoadReport", "audit", "compare_sequential", "decode", "encode",
           "max_safe_width", "region_loads", "region_of"]
