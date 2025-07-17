#pragma once

#include <stdint.h>


#define COMM_USER_DATA_TYPE           0xFF

#define SC64_SCR_REG                  (0x1FFF0000)
#define SC64_SCR_CMD_BUSY             (1 << 31)
#define SC64_SCR_CMD_ERROR            (1 << 30)
#define SC64_SCR_BTN_IRQ_PENDING      (1 << 29)
#define SC64_SCR_BTN_IRQ_MASK         (1 << 28)
#define SC64_SCR_CMD_IRQ_PENDING      (1 << 27)
#define SC64_SCR_CMD_IRQ_MASK         (1 << 26)
#define SC64_SCR_USB_IRQ_PENDING      (1 << 25)
#define SC64_SCR_USB_IRQ_MASK         (1 << 24)
#define SC64_SCR_AUX_IRQ_PENDING      (1 << 23)
#define SC64_SCR_AUX_IRQ_MASK         (1 << 22)
#define SC64_SCR_CMD_IRQ_REQUEST      (1 << 8)

#define SC64_DATA0_REG                (0x1FFF0004)
#define SC64_DATA1_REG                (0x1FFF0008)
#define SC64_IDENT_REG                (0x1FFF000C)
#define SC64_KEY_REG                  (0x1FFF0010)

#define SC64_IRQ_REG                  (0x1FFF0014)
#define SC64_IRQ_BTN_CLEAR            (1 << 31)
#define SC64_IRQ_CMD_CLEAR            (1 << 30)
#define SC64_IRQ_USB_CLEAR            (1 << 29)
#define SC64_IRQ_AUX_CLEAR            (1 << 28)
#define SC64_IRQ_USB_DISABLE          (1 << 11)
#define SC64_IRQ_USB_ENABLE           (1 << 10)
#define SC64_IRQ_AUX_DISABLE          (1 << 9)
#define SC64_IRQ_AUX_ENABLE           (1 << 8)

#define SC64_AUX_REG                  (0x1FFF0018)
#define SC64_AUX_PING                 (0xFF000000)
#define SC64_AUX_HALT                 (0xFF000001)
#define SC64_AUX_REBOOT               (0xFF000002)

typedef struct {
    uint16_t length;
    uint16_t type;
} pkt_info_hdr_t;
typedef void (*comm_handler_t)(const pkt_info_hdr_t *info);

void comm_init(const comm_handler_t *handlers, int16_t count);
void comm_task(void);
