#include <stdint.h>

#include <libdragon.h>


void graphics_draw_circle(surface_t *surf, int x, int y, int r, uint32_t color)
{
    int r_sqr = r * r;
    int cx = x + r;
    int cy = y + r;

    for (int x = -r; x <= r; x++) {
        int h = (int) sqrt(r_sqr - x * x);
        graphics_draw_line(surf, x + cx, -h + cy, x + cx, h + cy, color);
    }
}
