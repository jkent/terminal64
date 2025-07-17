#include <stdbool.h>

#include <libdragon.h>

#include "comm.h"
#include "game.h"
#include "graphics.h"
#include "util.h"


// IN to host
enum {
    GAME_IN_INPUT,
};

// OUT from host
enum {
    GAME_OUT_RESET,
    GAME_OUT_READY,
    GAME_OUT_ENTITY,
};

static void joypad_task(void);
static void game_out_reset(const comm_user_hdr_t *hdr);
static void game_out_ready(const comm_user_hdr_t *hdr);
static void game_out_entity(const comm_user_hdr_t *hdr);

comm_user_func_t game_comm_handlers[] = {
    [GAME_OUT_RESET]  = game_out_reset,
    [GAME_OUT_READY]  = game_out_ready,
    [GAME_OUT_ENTITY] = game_out_entity,
};

entity_t entities[256];
bool ready;

void game_setup(void)
{
    comm_init(game_comm_handlers, _countof(game_comm_handlers));
    display_init(RESOLUTION_320x240, DEPTH_32_BPP, 2, GAMMA_NONE, FILTERS_RESAMPLE);
    joypad_init();

    game_out_reset(NULL);
}

void game_loop(void)
{
    surface_t *display = display_get();
    graphics_fill_screen(display, 0x171717ff);

    float fps = display_get_fps();
    char s[10];
    sprintf(s, "FPS: %.1f", fps);
    graphics_set_color(0x999999ff, 0);
    graphics_draw_text(display, 16, 16, s);

    for (int idx = 0; idx < (ready ? _countof(entities) : 1); idx++) {
        entity_t *entity = &entities[idx];

        switch (entity->type) {
        case ENTITY_TYPE_NONE:
            break;

        case ENTITY_TYPE_RECT:
            graphics_draw_box(display, entity->rect.x, entity->rect.y,
                            entity->rect.width, entity->rect.height,
                            entity->color);
            break;

        case ENTITY_TYPE_BALL:
            graphics_draw_circle(display, entity->rect.x, entity->rect.y,
                                entity->rect.height / 2, entity->color);
            break;

        case ENTITY_TYPE_TEXT:
            graphics_set_color(entity->color, 0);
            graphics_draw_text(display, entity->rect.x, entity->rect.y,
                            entity->user);
            break;
        }
    }

    joypad_task();
    comm_task();
    comm_user_flush();

    display_show(display);
}

static void joypad_task(void)
{
    static joypad_inputs_t inputs_last;
    struct {
        comm_user_hdr_t hdr;
        joypad_inputs_t inputs;
    } pkt;

    joypad_poll();
    pkt.hdr.length = sizeof(pkt.inputs);
    pkt.hdr.type = GAME_IN_INPUT;
    pkt.inputs = joypad_get_inputs(JOYPAD_PORT_1);

    if (memcmp(&inputs_last, &pkt.inputs, sizeof(inputs_last))) {
        comm_user_write(&pkt, sizeof(pkt));
    }

    inputs_last = pkt.inputs;
}

static void game_out_reset(const comm_user_hdr_t *hdr)
{
    if (hdr) {
        comm_user_skip(hdr->length);
    }

    for (int idx = 0; idx < _countof(entities); idx++) {
        entity_t *entity = &entities[idx];
        entity->type = ENTITY_TYPE_NONE;
        free(entity->user);
        entity->user = NULL;
    }

    entities[0].type = ENTITY_TYPE_TEXT;
    entities[0].rect.x = display_get_width() / 2 - 17 * 8 / 2;
    entities[0].rect.y = display_get_height() / 2 - 4;
    entities[0].color = 0xffffffff;
    entities[0].user = strdup("Waiting for host!");

    ready = false;
}

static void game_out_ready(const comm_user_hdr_t *hdr)
{
    comm_user_skip(hdr->length);

    ready = true;
}

static void game_out_entity(const comm_user_hdr_t *hdr)
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

    comm_user_read(&pkt, sizeof(pkt));
    uint16_t data_len = hdr->length - sizeof(pkt);
    if (pkt.idx >= _countof(entities)) {
        comm_user_skip(data_len);
        return;
    }

    entity_t *entity = &entities[pkt.idx];
    memcpy(entity, &pkt.entity, sizeof(pkt.entity));
    free(entity->user);
    entity->user = NULL;
    if (data_len > 0) {
        entity->user = calloc(1, data_len + 1);
        if (entity->user) {
            comm_user_read(entity->user, data_len);
        } else {
            comm_user_skip(data_len);
        }
    }
}
