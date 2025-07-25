#include <stdint.h>
#include <string.h>

#include "util.h"


float float16_to_float(uint16_t value)
{
    uint32_t t1 = ((value & 0x7fffu) << 13u) + 0x38000000;
    uint32_t t2 = (value & 0x8000u) << 16;
    uint32_t t3 = (value & 0x7c00u);
    t1 = (t3 == 0 ? 0 : t1) | t2;

    union {
        uint32_t u;
        float f;
    } punner;
    punner.u = t1;
    return punner.f;
}

int vlq_pack(void *data, size_t max_length, uint32_t value)
{
    char *p = (char *) data;

    if (value < (1 << 7) && max_length >= 1) {
        *p++ =   value;
    } else if (value < (1 << 14) && max_length >= 2) {
        *p++ =  (value >>  7)         | 0x80;
        *p++ =   value        & 0x7f;
    } else if (value < (1 << 21) && max_length >= 3) {
        *p++ =  (value >> 14)         | 0x80;
        *p++ = ((value >>  7) & 0x7f) | 0x80;
        *p++ =   value        & 0x7f;
    } else if (value < (1 << 28) && max_length >= 4) {
        *p++ =  (value >> 21)         | 0x80;
        *p++ = ((value >> 14) & 0x7f) | 0x80;
        *p++ = ((value >>  7) & 0x7f) | 0x80;
        *p++ =   value        & 0x7f;
    } else if (max_length >= 5) {
        *p++ =  (value >> 28)         | 0x80;
        *p++ = ((value >> 21) & 0x7f) | 0x80;
        *p++ = ((value >> 14) & 0x7f) | 0x80;
        *p++ = ((value >>  7) & 0x7f) | 0x80;
        *p++ =   value        & 0x7f;
    }
    return (void *) p - data;
}

int vlq_unpack(uint32_t *value, const void *data, size_t data_length)
{
    *value = 0;
    size_t length = 0;
    const char *p = (const char *) data;

    while (length < data_length) {
        *value |= *p & 0x7f;
        if (!(*p++ & 0x80)) {
            return (const void *) p - data;
        }
        if ((const void *) p - data >= 5) {
            break;
        }
        *value <<= 7;
    }
    return -1;
}
