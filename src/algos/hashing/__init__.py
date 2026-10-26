from .pair_sum import find_pair_with_sum

__all__ = ["find_pair_with_sum"]

try:  # batch-версии нужен numpy (extra "fast")
    from .pair_sum_batch import find_pairs_batch

    __all__.append("find_pairs_batch")
except ImportError:
    pass
