#pragma once

#include <stdint.h>

#define _countof(x) (sizeof(x) / sizeof(x[0]))
#define BIT(n) (1 << (n))

typedef uint16_t float16;

float float16_to_float(float16);
