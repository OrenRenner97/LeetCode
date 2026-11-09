// Манакер (LeetCode 5) с отображением: a — коды элементов, b — коды их отражений (без mirror b == a).
// Виртуальная строка из 2n + 1 позиций: чётные — разделители (равны всегда), нечётные — a[i >> 1].
// out — 2n + 1 радиусов (длин палиндромов), выделяет Python.
//
// Пробовали вести расширение в индексах элементов (без проверки чётности, шаг 2): быстрее не стало,
// компилятор и так хорошо разворачивает этот цикл. Оставлена простая версия.
#include <stdint.h>

#define DEFINE_RADII(NAME, T)                                                               \
    void NAME(const T *a, const T *b, int64_t n, int use_mirror, int64_t *out) {           \
        const int64_t m = 2 * n + 1;                                                        \
        int64_t c = 0, r = 0;                                                               \
        for (int64_t i = 0; i < m; i++) {                                                   \
            if (use_mirror && (i & 1) && a[i >> 1] != b[i >> 1]) { out[i] = 0; continue; }  \
            int64_t k = 0;                                                                  \
            if (i < r) { k = out[2 * c - i]; if (k > r - i) k = r - i; }                    \
            int64_t lo = i - k - 1, hi = i + k + 1;                                         \
            while (lo >= 0 && hi < m && (!(lo & 1) || a[lo >> 1] == b[hi >> 1])) {         \
                lo--; hi++;                                                                 \
            }                                                                               \
            k = hi - i - 1;                                                                 \
            out[i] = k;                                                                     \
            if (i + k > r) { c = i; r = i + k; }                                            \
        }                                                                                   \
    }

DEFINE_RADII(palindrome_radii_i32, int32_t)  // строки: кодовые точки
DEFINE_RADII(palindrome_radii_i64, int64_t)  // массивы целых
