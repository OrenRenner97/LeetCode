// Самое длинное окно, где каждый id встречается <= k раз (LeetCode 3, обобщённо).
// ids — сжатые идентификаторы в [0, m). Результат: [*out_start, *out_end).
// Возвращает 0, или -1 при нехватке памяти.
#include <stdint.h>
#include <stdlib.h>

int longest_unique_window(const int64_t *ids, int64_t n, int64_t m, int64_t k,
                          int64_t *out_start, int64_t *out_end) {
    // k == 1: buf[x] = последняя позиция + 1 (0 = не встречался) → левый край прыгает.
    // k > 1:  buf[x] = сколько раз x в окне → левый край ползёт.
    int64_t *buf = calloc((size_t)(m > 0 ? m : 1), sizeof *buf);
    if (!buf) return -1;

    int64_t left = 0, best_start = 0, best_len = 0;
    for (int64_t r = 0; r < n; r++) {
        const int64_t x = ids[r];
        if (k == 1) {
            if (buf[x] > left) left = buf[x];  // buf[x] - 1 >= left  ⇔  buf[x] > left
            buf[x] = r + 1;
        } else {
            buf[x]++;
            while (buf[x] > k) buf[ids[left++]]--;
        }
        if (r - left + 1 > best_len) { best_start = left; best_len = r - left + 1; }
    }
    free(buf);
    *out_start = best_start;
    *out_end = best_start + best_len;
    return 0;
}
