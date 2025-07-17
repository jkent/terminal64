#pragma once

#include <stdint.h>


typedef struct {
    uint16_t length;
    uint16_t type;
} comm_user_hdr_t;
typedef void (*comm_user_func_t)(const comm_user_hdr_t *hdr);

void comm_init(const comm_user_func_t *handlers, int16_t count);
void comm_task(void);
void comm_user_read(void *data, uint16_t len);
void comm_user_skip(uint16_t len);
void comm_user_write(const void *data, uint16_t len);
void comm_user_flush(void);
