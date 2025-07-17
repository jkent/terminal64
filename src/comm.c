#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>
#include <usb.h>

#include "comm.h"


#define COMM_USER_DATA_TYPE           0xFF

static const comm_user_func_t *user_funcs = 0;
static int16_t user_func_count;
static char user_send_buf[4096];
static uint16_t user_send_buf_len;

void comm_init(const comm_user_func_t *funcs, int16_t count)
{
    user_funcs = funcs;
    user_func_count = count;
}

void comm_task(void)
{
    uint32_t usb_status = usb_poll();
    if (usb_status == 0) {
        return;
    }

    int type = usb_status >> 24;
    int remaining = usb_status & 0xffffff;
    if (type == COMM_USER_DATA_TYPE) {
        comm_user_hdr_t hdr;
        while (remaining >= sizeof(hdr)) {
            usb_read(&hdr, sizeof(hdr));
            if (sizeof(hdr) + hdr.length > remaining) {
                break;
            }
            remaining -= sizeof(hdr) + hdr.length;
            if (hdr.type >= user_func_count) {
                usb_skip(hdr.length);
                continue;
            }
            comm_user_func_t user_func = user_funcs[hdr.type];
            user_func(&hdr);
        }
    }
    usb_purge();
}

void comm_user_read(void *data, uint16_t len)
{
    usb_read(data, len);
}

void comm_user_skip(uint16_t len)
{
    usb_skip(len);
}

void comm_user_write(const void *data, uint16_t len)
{
    uint16_t remaining = sizeof(user_send_buf) - user_send_buf_len;

    if (remaining < len) {
        return;
    }
    memcpy(user_send_buf + user_send_buf_len, data, len);
    user_send_buf_len += len;
}

void comm_user_flush(void)
{
    if (user_send_buf_len > 0) {
        usb_write(COMM_USER_DATA_TYPE, user_send_buf, user_send_buf_len);
        user_send_buf_len = 0;
    }
}
