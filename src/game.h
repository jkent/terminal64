#pragma once

#include <stdint.h>

#include <libdragon.h>

typedef enum __packed {
    ENTITY_TYPE_FREE,
    ENTITY_TYPE_SPRITE,
    ENTITY_TYPE_RECTANGLE,
    ENTITY_TYPE_CIRCLE,
    ENTITY_TYPE_TEXT,
} entity_type_t;

typedef enum __packed {
    ENTITY_FLAGS_BLEND  = 1 << 0,
    ENTITY_FLAGS_FLIP_X = 1 << 4,
    ENTITY_FLAGS_FLIP_Y = 1 << 5,
} entity_flags_t;

typedef struct {
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;
} rect_t;

typedef struct {
    entity_type_t type;
    entity_flags_t flags;
    uint16_t idx;
    uint16_t x;
    uint16_t y;
    union {
        uint16_t width;
        uint16_t radius;
        uint16_t tile;
    };
    union {
        uint16_t height;
        uint16_t degrees;
    };
    uint32_t color;
    char data[0];
} entity_t;

void game_setup(void);
void game_loop(void);
