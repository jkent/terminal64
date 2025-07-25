#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#include <libdragon.h>
#include <usb.h>

#include "game.h"
#include "util.h"


int main(void)
{
    if (usb_initialize() == CART_NONE) {
        console_init();
        debug_init_usblog();
        console_set_debug(true);
        printf("Sorry, unsupported flash cart :(\n");
        while (1)
            ;
    }

    game_setup();

    while (true) {
        asm("wait");
        game_loop();
    }
}
