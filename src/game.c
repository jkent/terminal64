#include <malloc.h>
#include <stdbool.h>

#include <libdragon.h>

#include "game.h"
#include "graphics.h"
#include "usb/messages.h"
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
static void game_out_reset_message(size_t length);
static void game_out_ready_message(size_t length);
static void game_out_background_message(size_t length);
static void game_out_sprite_message(size_t length);
static void game_out_entity_message(size_t length);

usb_message_handler_t message_handlers[] = {
    [GAME_OUT_RESET]        = game_out_reset_message,
    [GAME_OUT_READY]        = game_out_ready_message,
    [GAME_OUT_BACKGROUND]   = game_out_background_message,
    [GAME_OUT_SPRITE]       = game_out_sprite_message,
    [GAME_OUT_ENTITY]       = game_out_entity_message,
};

static color_t background;
static void *sprites_buf[256];
static sprite_t *sprites[256];
static entity_t *entities[1024];
static bool waiting_for_host;

void game_setup(void)
{
    usb_messages_init(message_handlers, _countof(message_handlers));
    display_init(RESOLUTION_320x240, DEPTH_16_BPP, 3, GAMMA_NONE,
        FILTERS_DISABLED);

    rdpq_init();
    rdpq_font_t *font = rdpq_font_load_builtin(FONT_BUILTIN_DEBUG_MONO);
    rdpq_text_register_font(1, font);
    rdpq_font_style(font, 0, &(rdpq_fontstyle_t){
        .color = RGBA32(0xff, 0xff, 0xff, 0xff),
    });
    rdpq_font_style(font, 1, &(rdpq_fontstyle_t){
        .color = RGBA32(0x99, 0x99, 0x99, 0xff),
    });

    joypad_init();

    game_out_reset_message(0);
}

void game_loop(void)
{
    surface_t *disp = display_get();

    rdpq_attach(disp, NULL);
    rdpq_clear(background);

    if (waiting_for_host) {
        rdpq_text_print(&(rdpq_textparms_t){
            .style_id = 0,
            .width = display_get_width(),
            .height = display_get_height(),
            .align = ALIGN_CENTER,
            .valign = VALIGN_CENTER,
        }, 1, 0, 0,
        "Waiting for host!");
        rdpq_detach_show();
        usb_messages_task();
        return;
    }

    for (int i = 0; i < _countof(entities); i++) {
        entity_t *entity = entities[i];
        if (!entity) {
            continue;
        }

        switch (entity->type) {
            case ENTITY_TYPE_FREE:
                continue;

            case ENTITY_TYPE_SPRITE: {
                if (entity->sprite.index >= _countof(sprites)) {
                    break;
                }
                sprite_t *sprite = sprites[entity->sprite.index];
                if (!sprite) {
                    break;
                }
                int tile_width = sprite->width / sprite->hslices;
                int tile_height = sprite->height / sprite->vslices;
                int col = entity->sprite.tile % sprite->hslices;
                int row = entity->sprite.tile / sprite->hslices;
                rdpq_set_mode_standard();
                rdpq_mode_filter(FILTER_POINT);
                rdpq_mode_alphacompare(1);
                rdpq_sprite_blit(sprite, float16_to_float(entity->sprite.x),
                    float16_to_float(entity->sprite.y), &(rdpq_blitparms_t){
                        .s0 = tile_width * col,
                        .t0 = tile_height * row,
                        .width = tile_width,
                        .height = tile_height,
                        .flip_x = !!(entity->sprite.flags & ENTITY_SPRITE_FLIP_X),
                        .flip_y = !!(entity->sprite.flags & ENTITY_SPRITE_FLIP_Y),
                        .cx = entity->sprite.cx,
                        .cy = entity->sprite.cy,
                        .scale_x = float16_to_float(entity->sprite.scale_x),
                        .scale_y = float16_to_float(entity->sprite.scale_y),
                        .theta = float16_to_float(entity->sprite.theta),
                    });
                break;
            }

            case ENTITY_TYPE_RECTANGLE: {
                rdpq_set_mode_fill(color_from_packed16(entity->rectangle.color));
                rdpq_fill_rectangle(entity->rectangle.x0, entity->rectangle.y0,
                    entity->rectangle.x1, entity->rectangle.y1);
                break;
            }

            case ENTITY_TYPE_CIRCLE: {
                rdpq_set_mode_fill(color_from_packed16(entity->circle.color));
                rdpq_fill_circle(entity->circle.x, entity->circle.y,
                    entity->circle.radius);
                break;
            }

            case ENTITY_TYPE_TEXT: {
                rdpq_font_style((rdpq_font_t *) rdpq_text_get_font(1), 2,
                    &(rdpq_fontstyle_t){
                        .color = color_from_packed16(entity->text.color),
                    });
                rdpq_text_print(&(rdpq_textparms_t){
                        .style_id = 2,
                    }, 1, float16_to_float(entity->text.x),
                    float16_to_float(entity->text.y), entity->text.string);
                break;
            }
        }
    }

    rdpq_text_printf(&(rdpq_textparms_t){
        .style_id = 1,
    }, 1, 16, 16, "FPS: %.1f", display_get_fps());
    rdpq_detach_show();

    joypad_task();
    usb_messages_task();
}

static void joypad_task(void)
{
    static joypad_inputs_t inputs_last;
    joypad_inputs_t inputs;

    joypad_poll();
    inputs = joypad_get_inputs(JOYPAD_PORT_1);

    if (memcmp(&inputs_last, &inputs, sizeof(inputs_last))) {
        queue_usb_message(GAME_IN_INPUT, &inputs, sizeof(inputs));
    }
    inputs_last = inputs;
}

static void game_out_reset_message(size_t length)
{
    waiting_for_host = true;

    background = RGBA32(0x17, 0x17, 0x17, 0xff);

    for (int i = 0; i < _countof(sprites_buf); i++) {
        sprites[i] = NULL;
        free(sprites_buf[i]);
        sprites_buf[i] = NULL;
    }

    for (int i = 0; i < _countof(entities); i++) {
        free(entities[i]);
        entities[i] = NULL;
    }
}

static void game_out_ready_message(size_t length)
{
    waiting_for_host = false;
}

static void game_out_background_message(size_t length)
{
    struct {
        uint32_t color;
    } pkt;

    usb_messages_read(&pkt, sizeof(pkt));
    background = color_from_packed32(pkt.color);
}

static void game_out_sprite_message(size_t length)
{
    struct {
        uint16_t i;
    } pkt;

    usb_messages_read(&pkt, sizeof(pkt));
    uint16_t sprite_len = length - sizeof(pkt);
    if (pkt.i >= _countof(sprites_buf)) {
        usb_messages_skip(sprite_len);
        return;
    }

    if (sprite_len == 0) {
        sprites[pkt.i] = NULL;
        free(sprites_buf[pkt.i]);
        sprites_buf[pkt.i] = NULL;
        return;
    } else {
        void *p = realloc(sprites_buf[pkt.i], sprite_len);
        if (p == NULL) {
            usb_messages_skip(sprite_len);
            return;
        }
        sprites_buf[pkt.i] = p;
    }

    usb_messages_read(sprites_buf[pkt.i], sprite_len);
    sprites[pkt.i] = sprite_load_buf(sprites_buf[pkt.i], sprite_len);
}

static void game_out_entity_message(size_t length)
{
    struct {
        uint16_t i;
    } pkt;

    usb_messages_read(&pkt, sizeof(pkt));
    uint16_t entity_len = length - sizeof(pkt);
    if (pkt.i >= _countof(entities)) {
        usb_messages_skip(entity_len);
        return;
    }

    if (entity_len == 0) {
        free(entities[pkt.i]);
        entities[pkt.i] = NULL;
        return;
    } else {
        void *p = realloc(entities[pkt.i], entity_len);
        if (p == NULL) {
            usb_messages_skip(entity_len);
            return;
        }
        entities[pkt.i] = p;
    }

    if (entities[pkt.i]) {
        usb_messages_read(entities[pkt.i], entity_len);
    } else {
        usb_messages_skip(entity_len);
    }
}
