#include <stddef.h>
#include <stdint.h>

#include <libdragon.h>
#include <usb.h>

#include "messages.h"
#include "../util.h"


static char msg_buf[4096];
static size_t msg_buf_length = 0;
static const usb_message_handler_t *msg_handlers = 0;
static size_t msg_handler_count = 0;

void usb_messages_init(const usb_message_handler_t *handlers, size_t count)
{
    msg_handlers = handlers;
    msg_handler_count = count;
}

void usb_messages_task(void)
{
    if (msg_buf_length > 0) {
        usb_write(0xff, msg_buf, msg_buf_length);
        msg_buf_length = 0;
    }

    uint32_t usb_status = usb_poll();
    if (usb_status == 0) {
        return;
    }

    char buf[10];
    uint8_t packet_type = usb_status >> 24;
    size_t packet_length = usb_status & 0xffffff;

    if (packet_type == 0xff) {
        int read, pos, ret;
        uint32_t message_type;
        uint32_t message_length;
        while (packet_length > 0) {
            read = MIN(sizeof(buf), packet_length);
            pos = 0;
            usb_read(buf, read);
            ret = vlq_unpack(&message_type, buf, read - pos);
            assert(ret > 0);
            pos += ret;
            ret = vlq_unpack(&message_length, &buf[pos], read - pos);
            assert(ret > 0);
            pos += ret;
            usb_rewind(read - pos);
            if (message_type >= msg_handler_count) {
                usb_skip(message_length);
            } else {
                msg_handlers[message_type](message_length);
            }
            packet_length -= pos + message_length;
        }
    }
    usb_purge();
}

void usb_messages_read(void *data, size_t length)
{
    usb_read(data, length);
}

void usb_messages_skip(size_t length)
{
    usb_skip(length);
}

void queue_usb_message(uint32_t type, const void *data, size_t length)
{
    char buf[10], *p = buf;
    int ret;

    ret = vlq_pack(p, sizeof(buf) - (p - buf), type);
    assert(ret > 0);
    p += ret;
    ret = vlq_pack(p, sizeof(buf) - (p - buf), length);
    assert(ret > 0);
    p += ret;

    if (p - buf + length > sizeof(msg_buf) - msg_buf_length) {
        return;
    }

    memcpy(&msg_buf[msg_buf_length], buf, p - buf);
    msg_buf_length += p - buf;
    memcpy(&msg_buf[msg_buf_length], data, length);
    msg_buf_length += length;
}
