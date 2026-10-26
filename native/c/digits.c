// Длинное сложение: out[0..na) = a + b (b дополнен нулями до na, na >= nb).
// Возвращает перенос из старшего разряда (0 или 1).
// base == 0 означает 2^64 (лимбы целиком), иначе 2 <= base <= 2^63.
#include <stdint.h>
#include <string.h>
#if defined(__x86_64__)
#include <immintrin.h>
#endif

int add_digits_u64(const uint64_t *a, int64_t na, const uint64_t *b, int64_t nb, uint64_t base, uint64_t *out) {
    unsigned char c = 0;
    int64_t k = 0;

    if (base == 0) {
#if defined(__x86_64__)
        // _addcarry_u64 компилируется в инструкцию ADC: процессор сам несёт перенос через флаг CF.
        // Это и есть «сложение столбиком», только в железе и по 64 бита за такт.
        unsigned long long r;
        for (; k < nb; k++) { c = _addcarry_u64(c, a[k], b[k], &r); out[k] = r; }
        for (; k < na && c; k++) { c = _addcarry_u64(c, a[k], 0, &r); out[k] = r; }
#else
        for (; k < nb; k++) {
            uint64_t s = a[k] + b[k], s2 = s + c;
            c = (s < a[k]) | (s2 < s);
            out[k] = s2;
        }
        for (; k < na && c; k++) { out[k] = a[k] + 1; c = out[k] == 0; }
#endif
    } else {
        // a, b < base <= 2^63 → сумма < 2^64, переполнения uint64 нет.
        for (; k < nb; k++) {
            uint64_t s = a[k] + b[k] + c;
            c = s >= base;
            out[k] = c ? s - base : s;
        }
        for (; k < na && c; k++) {
            uint64_t s = a[k] + 1;
            c = s == base;
            out[k] = c ? 0 : s;
        }
    }

    if (k < na) memcpy(out + k, a + k, (size_t)(na - k) * sizeof *out);  // перенос погас: хвост копируем
    return c;
}
