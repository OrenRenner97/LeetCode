"""Библиотека алгоритмов. Модули организованы по технике, а не по номеру задачи LeetCode."""
from ._dispatch import BackendUnavailable
from .arithmetic import add_digits
from .hashing import find_pair_with_sum
from .sliding_window import longest_unique_window

__all__ = ["BackendUnavailable", "add_digits", "find_pair_with_sum", "longest_unique_window"]
