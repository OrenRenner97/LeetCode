// Two Sum: hash one-pass на открытой адресации (линейное пробирование).
// Контракт как у algos.find_pair_with_sum: минимальный j, затем минимальный i.
// Ограничение: |values|, |target| < 2^62, чтобы target - x не переполнялся в int64.
#include <stdint.h>
#include <stdlib.h>

// Ключ и индекс в одной ячейке (16 байт, 4 ячейки на cache line): одна проба = один промах кэша.
// С раздельными массивами keys[] / pos[] промахов было бы два.
typedef struct {
    int64_t key;
    int64_t pos;  // индекс + 1, 0 = пусто
} Slot;

static inline uint64_t slot(int64_t key, int shift) {
    // Fibonacci hashing: старшие биты произведения на 2^64 / φ.
    return ((uint64_t)key * 0x9E3779B97F4A7C15ULL) >> shift;
}

// Возвращает 1 и пишет (i, j) в out, если пара есть; 0, если нет; -1 при нехватке памяти.
int pair_sum(const int64_t *values, int64_t n, int64_t target, int64_t *out_i, int64_t *out_j) {
    int bits = 1;
    while (((int64_t)1 << bits) < n + n / 2 + 1) bits++;  // load factor ≤ 2/3
    const uint64_t mask = ((uint64_t)1 << bits) - 1;
    const int shift = 64 - bits;

    // calloc получает нулевые страницы от ОС лениво,
    // поэтому при раннем выходе огромная таблица почти ничего не стоит.
    Slot *t = calloc(mask + 1, sizeof *t);
    if (!t) return -1;

    int found = 0;
    for (int64_t j = 0; j < n; j++) {
        const int64_t x = values[j], need = target - x;

        for (uint64_t h = slot(need, shift); t[h].pos; h = (h + 1) & mask) {
            if (t[h].key == need) { *out_i = t[h].pos - 1; *out_j = j; found = 1; goto done; }
        }

        uint64_t h = slot(x, shift);
        while (t[h].pos && t[h].key != x) h = (h + 1) & mask;
        if (!t[h].pos) { t[h].key = x; t[h].pos = j + 1; }  // храним только первое вхождение
    }

done:
    free(t);
    return found;
}
