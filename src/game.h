#pragma once

#include <stdint.h>

#include <libdragon.h>

typedef enum {
    ENTITY_TYPE_NONE,
    ENTITY_TYPE_RECT,
    ENTITY_TYPE_BALL,
    ENTITY_TYPE_TEXT,
} entity_type_t;

typedef struct {
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;
} rect_t;

typedef struct {
    uint16_t type;
    uint16_t flags;
    rect_t rect;
    uint32_t color;
    void *user;
} entity_t;

extern entity_t entities[];

void game_setup(void);
void game_loop(void);
