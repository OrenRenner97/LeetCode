"""Самое длинное окно без лишних повторов. LeetCode: 3. Longest Substring Without Repeating Characters (обобщённо)."""
from collections.abc import Hashable, Sequence

from .._dispatch import Dispatcher

# benchmarks/longest_substring_backends.py: numba ≈ C (×20 к python на 10^6); векторный numpy и GPU
# (O(n log n) через накопленный максимум) медленнее даже python → только явно.
_dispatch = Dispatcher("longest_unique_window", priority=("numba", "c", "python", "numpy", "cuda"))


def longest_unique_window(
    seq: Sequence[Hashable], *, max_repeats: int = 1, backend: str | None = None
) -> tuple[int, int]:
    """Полуинтервал [start, end) самого длинного окна, где каждый элемент встречается не больше max_repeats раз.

    seq — любая последовательность хэшируемых элементов: строка, список id, кортежи событий.
    Нативные backend'ы (numba, c, numpy, cuda) работают с одномерными массивами int или str;
    auto включает их только для numpy-массивов: список Python-объектов дешевле обработать на Python,
    чем конвертировать.
    Длина ответа: end - start. Пустой seq → (0, 0).
    Если самых длинных окон несколько, возвращается самое левое.
    O(n) по времени, O(число различных элементов) по памяти.

    ValueError: max_repeats < 1.
    """
    if max_repeats < 1:
        raise ValueError(f"max_repeats должен быть >= 1, получено {max_repeats}")
    n_for_auto = len(seq) if hasattr(seq, "dtype") else 0  # не массив → auto выберет python
    return _dispatch.resolve(backend, n_for_auto)(seq, max_repeats)


@_dispatch.register("python")
def _python(seq: Sequence[Hashable], max_repeats: int) -> tuple[int, int]:
    return _last_index(seq) if max_repeats == 1 else _counts(seq, max_repeats)


def _last_index(seq: Sequence[Hashable]) -> tuple[int, int]:
    # k = 1: левый край прыгает сразу за прошлое вхождение (оптимум из задачи 3).
    last: dict[Hashable, int] = {}
    left = best_start = best_len = 0
    for right, x in enumerate(seq):
        prev = last.get(x, -1)
        if prev >= left:  # прошлое вхождение внутри окна; без этой проверки «abba» сломает окно
            left = prev + 1
        last[x] = right
        if right - left + 1 > best_len:  # строго больше → при равенстве остаётся самое левое окно
            best_start, best_len = left, right - left + 1
    return best_start, best_start + best_len


def _counts(seq: Sequence[Hashable], k: int) -> tuple[int, int]:
    # k > 1: прыгнуть нельзя (неясно, какое вхождение выкинуть), поэтому левый край ползёт.
    # Каждый элемент входит и выходит по разу → всё равно O(n).
    count: dict[Hashable, int] = {}
    left = best_start = best_len = 0
    for right, x in enumerate(seq):
        count[x] = count.get(x, 0) + 1
        while count[x] > k:
            count[seq[left]] -= 1
            left += 1
        if right - left + 1 > best_len:
            best_start, best_len = left, right - left + 1
    return best_start, best_start + best_len


_dispatch.register_optional("numba", "algos._native.numba_impl", "longest_unique_window_numba", min_n=1)
_dispatch.register_optional("c", "algos._native.c_impl", "longest_unique_window_c", min_n=1)
_dispatch.register_optional("numpy", "algos._native.vectorized", "unique_window_numpy", min_n=2**62)
_dispatch.register_optional("cuda", "algos._native.cuda_impl", "unique_window_cupy", min_n=2**62)

longest_unique_window.backends = _dispatch.available  # type: ignore[attr-defined]
