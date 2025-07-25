#include <stddef.h>
#include <stdint.h>


typedef void (*usb_message_handler_t)(size_t length);

void usb_messages_init(const usb_message_handler_t *handlers, size_t count);
void usb_messages_task(void);
void usb_messages_read(void *data, size_t length);
void usb_messages_skip(size_t length);
void queue_usb_message(uint32_t type, const void *data, size_t length);
