"""Выбор реализации алгоритма: python / numpy / numba / c / cuda.

Как выбирается backend:
  1. явный аргумент:          find_pair_with_sum(..., backend="c")
  2. переменная окружения:    ALGOS_BACKEND=numba
  3. "auto":                  первая доступная реализация в порядке priority,
                              у которой min_n <= размер входа.
                              Порядок и пороги подобраны по бенчмаркам (benchmarks/).

Бизнес-слой о нативном коде не знает: он передаёт строку backend или не передаёт ничего.
"""
import importlib
import os
from collections.abc import Callable

class BackendUnavailable(RuntimeError):
    pass


class Dispatcher:
    def __init__(self, name: str, priority: tuple[str, ...] = ("numba", "c", "cuda", "numpy", "python")):
        self.name = name
        self.priority = priority
        self._impls: dict[str, Callable] = {}
        self._min_n: dict[str, int] = {}
        self.import_errors: dict[str, str] = {}  # почему backend недоступен (для отладки)

    def register(self, backend: str, *, min_n: int = 0):
        """min_n: с какого размера входа "auto" выбирает этот backend.
        На маленьких входах накладные расходы FFI / копирования на GPU съедают выигрыш."""
        if backend not in self.priority:
            raise ValueError(f"unknown backend {backend!r}, expected one of {self.priority}")

        def deco(fn: Callable) -> Callable:
            self._impls[backend] = fn
            self._min_n[backend] = min_n
            return fn

        return deco

    def register_optional(self, backend: str, module: str, attr: str, *, min_n: int = 0) -> None:
        """Регистрирует backend, только если модуль импортируется (есть numba, собран .so, есть GPU)."""
        try:
            fn = getattr(importlib.import_module(module), attr)
        except Exception as e:  # ImportError, OSError (нет .so), ошибки инициализации CUDA
            self.import_errors[backend] = f"{type(e).__name__}: {e}"
            return
        self.register(backend, min_n=min_n)(fn)

    @property
    def available(self) -> list[str]:
        return [b for b in self.priority if b in self._impls]

    def resolve(self, backend: str | None = None, n: int | None = None) -> Callable:
        backend = backend or os.environ.get("ALGOS_BACKEND") or "auto"
        if backend == "auto":
            for b in self.available:
                if n is None or n >= self._min_n[b]:
                    return self._impls[b]
            return self._impls[self.available[-1]]
        try:
            return self._impls[backend]
        except KeyError:
            raise BackendUnavailable(
                f"{self.name}: backend {backend!r} недоступен, есть {self.available}"
            ) from None
