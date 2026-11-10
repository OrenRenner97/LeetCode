"""Библиотека алгоритмов. Модули организованы по технике, а не по номеру задачи LeetCode."""
from ._dispatch import BackendUnavailable
from .arithmetic import add_digits
from .binary_search import kth_of_many_sorted, kth_of_sorted, kth_of_two_sorted, median_of_sorted
from .hashing import find_pair_with_sum
from .palindromes import longest_palindrome
from .permutations import zigzag_decode, zigzag_encode
from .sliding_window import longest_unique_window

__all__ = ["BackendUnavailable", "add_digits", "find_pair_with_sum", "kth_of_many_sorted", "kth_of_sorted", "kth_of_two_sorted",
           "longest_palindrome", "median_of_sorted", "longest_unique_window", "zigzag_decode", "zigzag_encode"]
