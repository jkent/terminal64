#include <malloc.h>
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
    GAME_OUT_BACKGROUND,
    GAME_OUT_SPRITE,
    GAME_OUT_ENTITY,
};

static void joypad_task(void);
static void game_out_reset(const comm_user_hdr_t *hdr);
static void game_out_ready(const comm_user_hdr_t *hdr);
static void game_out_background(const comm_user_hdr_t *hdr);
static void game_out_sprite(const comm_user_hdr_t *hdr);
static void game_out_entity(const comm_user_hdr_t *hdr);

comm_user_func_t game_comm_handlers[] = {
    [GAME_OUT_RESET]        = game_out_reset,
    [GAME_OUT_READY]        = game_out_ready,
    [GAME_OUT_BACKGROUND]   = game_out_background,
    [GAME_OUT_SPRITE]       = game_out_sprite,
    [GAME_OUT_ENTITY]       = game_out_entity,
};

static color_t background;
static sprite_t *sprites[256] = {0};
static entity_t *entities[1024] = {0};
static bool waiting_for_host;

void game_setup(void)
{
    comm_init(game_comm_handlers, _countof(game_comm_handlers));
    display_init(RESOLUTION_320x240, DEPTH_16_BPP, 2, GAMMA_NONE, FILTERS_DISABLED);
    joypad_init();

    game_out_reset(NULL);
}

void game_loop(void)
{
    surface_t *display = display_get();

    graphics_fill_screen(display, graphics_convert_color(background));

    float fps = display_get_fps();
    char s[10];
    sprintf(s, "FPS: %.1f", fps);
    color_t color = RGBA32(0x99, 0x99, 0x99, 0xFF);
    graphics_set_color(graphics_convert_color(color), 0);
    graphics_draw_text(display, 16, 16, s);

    if (waiting_for_host) {
        const char *s = "Waiting for host!";
        uint16_t x = display_get_width() / 2 - strlen(s) * 8 / 2;
        uint16_t y = display_get_height() / 2 - 8 / 4;
        color_t color = RGBA32(0xff, 0xff, 0xff, 0xff);
        graphics_set_color(graphics_convert_color(color), 0);
        graphics_draw_text(display, x, y, s);
    } else {
        for (int i = 0; i < _countof(entities); i++) {
            entity_t *entity = entities[i];
            if (!entity) {
                continue;
            }

            switch (entity->type) {
                case ENTITY_TYPE_FREE:
                    continue;

                case ENTITY_TYPE_SPRITE: {
                    if (entity->idx >= _countof(sprites)) {
                        break;
                    }
                    sprite_t *sprite = sprites[entity->idx];
                    if (!sprite) {
                        break;
                    }
                    if (entity->flags & ENTITY_FLAGS_TRANS) {
                        graphics_draw_sprite_trans_stride(display, entity->x,
                            entity->y, sprite, entity->stride);
                    } else {
                        graphics_draw_sprite_stride(display, entity->x,
                            entity->y, sprite, entity->stride);
                    }
                    break;
                }

                case ENTITY_TYPE_RECTANGLE: {
                    color_t color = color_from_packed32(entity->color);
                    if (entity->flags & ENTITY_FLAGS_TRANS) {
                        graphics_draw_box_trans(display, entity->x, entity->y,
                            entity->height, entity->width,
                            graphics_convert_color(color));
                    } else {
                        graphics_draw_box(display, entity->x, entity->y,
                            entity->width, entity->height,
                            graphics_convert_color(color));
                    }
                    break;
                }

                case ENTITY_TYPE_CIRCLE: {
                    color_t color = color_from_packed32(entity->color);
                    graphics_draw_circle(display, entity->x, entity->y,
                        entity->r, graphics_convert_color(color));
                    break;
                }

                case ENTITY_TYPE_TEXT: {
                    color_t color = color_from_packed32(entity->color);
                    graphics_set_color(graphics_convert_color(color), 0);
                    graphics_draw_text(display, entity->x, entity->y,
                        entity->data);
                    break;
                }
            }
        }

        joypad_task();
    }

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
    waiting_for_host = true;

    background = RGBA32(0x17, 0x17, 0x17, 0xff);

    for (int i = 0; i < _countof(sprites); i++) {
        if (!sprites[i]) {
            continue;
        }
        free(sprites[i]);
        sprites[i] = NULL;
    }

    for (int i = 0; i < _countof(entities); i++) {
        if (!entities[i]) {
            continue;
        }
        free(entities[i]);
        entities[i] = NULL;
    }
}

static void game_out_ready(const comm_user_hdr_t *hdr)
{
    waiting_for_host = false;
}

static void game_out_background(const comm_user_hdr_t *hdr)
{
    struct {
        uint32_t color;
    } pkt;

    comm_user_read(&pkt, sizeof(pkt));
    background = color_from_packed32(pkt.color);
}

static void game_out_sprite(const comm_user_hdr_t *hdr)
{
    struct {
        uint16_t i;
    } pkt;

    comm_user_read(&pkt, sizeof(pkt));
    uint16_t sprite_len = hdr->length - sizeof(pkt);
    if (pkt.i >= _countof(sprites)) {
        comm_user_skip(sprite_len);
        return;
    }

    if (sprite_len == 0) {
        if (sprites[pkt.i]) {
            free(sprites[pkt.i]);
            sprites[pkt.i] = NULL;
        }
        return;
    } else {
        void *p = realloc(sprites[pkt.i], sprite_len);
        if (p == NULL) {
            comm_user_skip(sprite_len);
            return;
        }
        sprites[pkt.i] = p;
    }

    comm_user_read(sprites[pkt.i], sprite_len);
}

static void game_out_entity(const comm_user_hdr_t *hdr)
{
    struct {
        uint16_t i;
    } pkt;

    comm_user_read(&pkt, sizeof(pkt));
    uint16_t entity_len = hdr->length - sizeof(pkt);
    if (pkt.i >= _countof(entities)) {
        comm_user_skip(entity_len);
        return;
    }

    if (entity_len == 0) {
        if (entities[pkt.i]) {
            free(entities[pkt.i]);
            entities[pkt.i] = NULL;
        }
        return;
    } else if (entities[pkt.i]) {
        void *p = realloc(entities[pkt.i], entity_len);
        if (p == NULL) {
            comm_user_skip(entity_len);
            return;
        }
        entities[pkt.i] = p;
    } else {
        entities[pkt.i] = malloc(entity_len);
    }

    if (entities[pkt.i]) {
        comm_user_read(entities[pkt.i], entity_len);
    } else {
        comm_user_skip(entity_len);
    }
}
