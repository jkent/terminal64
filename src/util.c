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
