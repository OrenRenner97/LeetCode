// k-й элемент объединения отсортированных int64-массивов (LeetCode 4, обобщённо).
#include <stdint.h>

// Число элементов <= x. Без ветвлений в цикле: компилятор делает cmov, предсказатель переходов
// не ошибается на случайных данных (обычный бинпоиск ошибается в ~половине шагов).
static int64_t upper_bound(const int64_t *a, int64_t n, int64_t x) {
    if (n == 0) return 0;
    const int64_t *base = a;
    while (n > 1) {
        const int64_t half = n / 2;
        base = (base[half] <= x) ? base + half : base;
        n -= half;
    }
    return (base - a) + (*base <= x);
}

// Разрез из задачи 4: слева ровно need элементов (1 <= need <= m + n).
// *left = max слева, *right = min справа. Возвращает 1, если справа что-то есть, 0 — если нет,
// -1 — разрез не найден (недостижимо даже на неотсортированном входе, см. sorted_union.py).
int kth_two_i64(const int64_t *a, int64_t m, const int64_t *b, int64_t n, int64_t need,
                int64_t *left, int64_t *right) {
    if (m > n) {
        const int64_t *t = a; a = b; b = t;
        int64_t tn = m; m = n; n = tn;
    }
    int64_t lo = need > n ? need - n : 0, hi = need < m ? need : m;
    while (lo <= hi) {
        const int64_t i = lo + (hi - lo) / 2, j = need - i;
        if (i > 0 && j < n && a[i - 1] > b[j]) {
            hi = i - 1;
        } else if (j > 0 && i < m && b[j - 1] > a[i]) {
            lo = i + 1;
        } else {
            if (i == 0) *left = b[j - 1];
            else if (j == 0) *left = a[i - 1];
            else *left = a[i - 1] > b[j - 1] ? a[i - 1] : b[j - 1];
            if (i == m && j == n) return 0;
            if (i == m) *right = b[j];
            else if (j == n) *right = a[i];
            else *right = a[i] < b[j] ? a[i] : b[j];
            return 1;
        }
    }
    return -1;
}

// Бинпоиск по значению: наименьшее x, при котором элементов <= x больше k (0 <= k < Σ lens).
// arrs[q] — указатель на q-й массив длины lens[q] > 0.
int64_t kth_many_i64(const int64_t *const *arrs, const int64_t *lens, int64_t K, int64_t k) {
    int64_t lo = arrs[0][0], hi = arrs[0][lens[0] - 1];
    for (int64_t q = 1; q < K; q++) {
        if (arrs[q][0] < lo) lo = arrs[q][0];
        if (arrs[q][lens[q] - 1] > hi) hi = arrs[q][lens[q] - 1];
    }
    while (lo < hi) {
        // floor((lo + hi) / 2) без переполнения int64 (lo + hi вышло бы за 2^63)
        const int64_t mid = (lo >> 1) + (hi >> 1) + (lo & hi & 1);
        int64_t c = 0;
        for (int64_t q = 0; q < K; q++) c += upper_bound(arrs[q], lens[q], mid);
        if (c > k) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
