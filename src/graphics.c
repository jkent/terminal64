#include <libdragon.h>

#include "graphics.h"


void rdpq_fill_circle(int x, int y, int r)
{
    int r_sqr = r * r;
    int cx = x + r;
    int cy = y + r;

    for (int x = -r; x <= r; x++) {
        int h = (int) sqrt(r_sqr - x * x);
        rdpq_fill_rectangle(cx + x, cy - h, cx + x + 1, cy + h);
    }
}
