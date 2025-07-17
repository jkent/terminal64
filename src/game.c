#include <stdbool.h>

#include <libdragon.h>
#include <usb.h>

#include "comm.h"
#include "game.h"
#include "graphics.h"
#include "util.h"

// Send types
enum {
    COMM_INPUT_UPDATE,
};

// Receive types
enum {
    COMM_ENTITY,
};

static void game_comm_entity(const pkt_info_hdr_t *info);

comm_handler_t game_comm_handlers[] = {
    [COMM_ENTITY] = game_comm_entity,
};

entity_t entities[256];

void game_init(void)
{
    comm_init(game_comm_handlers, _countof(game_comm_handlers));
    display_init(RESOLUTION_320x240, DEPTH_32_BPP, 2, GAMMA_NONE, FILTERS_RESAMPLE);
    joypad_init();

    for (int idx = 0; idx < _countof(entities); idx++) {
        entities[idx].type = ENTITY_NONE;
    }

    entities[0].type = ENTITY_TEXT;
    entities[0].rect.x = display_get_width() / 2 - 24;
    entities[0].rect.y = display_get_height() / 2 - 4;
    entities[0].color = 0xffffffff;
    entities[0].user = strdup("Ready!");
}

void game_loop(void)
{
    static joypad_inputs_t inputs_last = {0};

    surface_t *display = display_get();
    graphics_fill_screen(display, 0x333333ff);

    float fps = display_get_fps();
    char s[10];
    sprintf(s, "FPS: %.1f", fps);
    graphics_set_color(0x999999ff, 0);
    graphics_draw_text(display, 16, 16, s);

    for (int idx = 0; idx < _countof(entities); idx++) {
        entity_t *entity = &entities[idx];

        switch (entity->type) {
        case ENTITY_NONE:
            break;

        case ENTITY_RECT:
            graphics_draw_box(display, entity->rect.x, entity->rect.y,
                            entity->rect.width, entity->rect.height,
                            entity->color);
            break;

        case ENTITY_BALL:
            graphics_draw_circle(display, entity->rect.x, entity->rect.y,
                                entity->rect.height / 2, entity->color);
            break;

        case ENTITY_TEXT:
            graphics_set_color(entity->color, 0);
            graphics_draw_text(display, entity->rect.x, entity->rect.y,
                               entity->user);
            break;
        }
    }

    display_show(display);

    {
        joypad_poll();
        struct {
            struct {
                uint16_t length;
                uint16_t type;
            } info;
            joypad_inputs_t inputs;
        } pkt;
        pkt.info.length = sizeof(pkt.inputs);
        pkt.info.type = COMM_INPUT_UPDATE;
        pkt.inputs = joypad_get_inputs(JOYPAD_PORT_1);
        if (memcmp(&inputs_last, &pkt.inputs, sizeof(inputs_last))) {
            usb_write(COMM_USER_DATA_TYPE, &pkt, sizeof(pkt));
        }
        inputs_last = pkt.inputs;
    }

    comm_task();
}

static void game_comm_entity(const pkt_info_hdr_t *info)
{
    struct {
        uint32_t idx;
        struct {
            uint16_t type;
            uint16_t flags;
            rect_t rect;
            uint32_t color;
        } entity;
    } pkt;

    usb_read(&pkt, sizeof(pkt));
    uint16_t data_len = info->length - sizeof(pkt);
    if (pkt.idx >= _countof(entities)) {
        usb_skip(data_len);
        return;
    }

    entity_t *entity = &entities[pkt.idx];
    memcpy(entity, &pkt.entity, sizeof(pkt.entity));
    free(entity->user);
    entity->user = NULL;
    if (data_len > 0) {
        entity->user = calloc(1, data_len + 1);
        if (entity->user) {
            usb_read(entity->user, data_len);
        } else {
            usb_skip(data_len);
        }
    }
}
