#pragma once

#include <stdint.h>

#define _countof(x) (sizeof(x) / sizeof(x[0]))

#define MIN(a, b) ({ \
    typeof (a) _a = (a); \
    typeof (b) _b = (b); \
    _a < _b ? _a : _b; \
})

#define MAX(a, b) ({ \
    typeof (a) _a = (a); \
    typeof (b) _b = (b); \
    _a > _b ? _a : _b; \
})

#define BIT(n) (1 << (n))

typedef uint16_t float16;

float float16_to_float(float16);
int vlq_pack(void *data, size_t max_length, uint32_t value);
int vlq_unpack(uint32_t *value, const void *data, size_t data_length);
