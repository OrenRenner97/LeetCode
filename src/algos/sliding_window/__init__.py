from .unique_window import longest_unique_window

__all__ = ["longest_unique_window"]

try:  # batch-версии нужен numpy (extra "fast")
    from .unique_window_batch import longest_unique_window_batch

    __all__.append("longest_unique_window_batch")
except ImportError:
    pass
