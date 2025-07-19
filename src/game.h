#pragma once

#include <stdint.h>

#include <libdragon.h>

#include "util.h"

typedef enum __packed {
    ENTITY_TYPE_FREE,
    ENTITY_TYPE_SPRITE,
    ENTITY_TYPE_RECTANGLE,
    ENTITY_TYPE_CIRCLE,
    ENTITY_TYPE_TEXT,
} entity_type_t;

typedef enum __packed {
    ENTITY_SPRITE_FLIP_X = BIT(0),
    ENTITY_SPRITE_FLIP_Y = BIT(1),
} entity_sprite_flags_t;

typedef struct __packed {
    entity_type_t type;
    union {
        struct __packed {
            uint8_t index;
            uint8_t tile;
            float16 x;
            float16 y;
            entity_sprite_flags_t flags;
            uint8_t cx;
            uint8_t cy;
            float16 scale_x;
            float16 scale_y;
            float16 theta;
        } sprite;
        struct __packed {
            uint32_t x0 : 12;
            uint32_t y0 : 12;
            uint32_t x1 : 12;
            uint32_t y1 : 12;
            uint16_t color;
        } rectangle;
        struct __packed {
            uint32_t x : 12;
            uint32_t y : 12;
            uint8_t radius;
            uint16_t color;
        } circle;
        struct __packed {
            float16 x;
            float16 y;
            uint32_t width : 12;
            uint32_t height : 12;
            uint8_t flags;
            uint16_t color;
            char string[0];
        } text;
    };
} entity_t;

void game_setup(void);
void game_loop(void);
