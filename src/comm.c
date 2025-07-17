#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>
#include <usb.h>

#include "comm.h"


#define COMM_USER_DATA_TYPE           0xFF

static int16_t handler_count;
static const comm_handler_t *comm_handlers = 0;

void comm_init(const comm_handler_t *handlers, int16_t count)
{
    comm_handlers = handlers;
    handler_count = count;
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
        pkt_info_hdr_t hdr;
        while (remaining >= sizeof(hdr)) {
            usb_read(&hdr, sizeof(hdr));
            if (sizeof(hdr) + hdr.length > remaining) {
                break;
            }
            remaining -= sizeof(hdr) + hdr.length;
            if (hdr.type >= handler_count) {
                usb_skip(hdr.length);
                continue;
            }
            comm_handler_t comm_handler = comm_handlers[hdr.type];
            comm_handler(&hdr);
        }
    }
    usb_purge();
}
