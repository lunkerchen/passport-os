#include "lvgl.h"
#include <stdint.h>
#include <string.h>
#include "zh_tw_glyph_map.h"

void __real_lv_label_set_text(lv_obj_t *obj, const char *text);
void __real_lv_label_set_text_static(lv_obj_t *obj, const char *text);

static uint16_t traditional(uint16_t cp)
{
    size_t lo = 0, hi = sizeof(zh_tw_map) / sizeof(zh_tw_map[0]);
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (zh_tw_map[mid][0] < cp) lo = mid + 1;
        else hi = mid;
    }
    return lo < sizeof(zh_tw_map) / sizeof(zh_tw_map[0]) && zh_tw_map[lo][0] == cp
        ? zh_tw_map[lo][1] : cp;
}

// CJK mappings below preserve the three-byte UTF-8 width. Only the displayed
// copy changes; SSIDs, saved names, API search keys and server replies stay intact.
static char *display_copy(const char *text)
{
    if (!text) return NULL;
    size_t length = strlen(text);
    char *copy = NULL;
    for (size_t i = 0; i + 2 < length; ++i) {
        const unsigned char *s = (const unsigned char *)text + i;
        if ((s[0] & 0xf0) != 0xe0 || (s[1] & 0xc0) != 0x80 || (s[2] & 0xc0) != 0x80) continue;
        uint16_t cp = ((s[0] & 15) << 12) | ((s[1] & 63) << 6) | (s[2] & 63);
        uint16_t out = traditional(cp);
        if (cp != out) {
            if (!copy) {
                copy = lv_malloc(length + 1);
                if (!copy) return NULL;
                memcpy(copy, text, length + 1);
            }
            copy[i] = 0xe0 | (out >> 12);
            copy[i + 1] = 0x80 | ((out >> 6) & 63);
            copy[i + 2] = 0x80 | (out & 63);
        }
        i += 2;
    }
    return copy;
}

void __wrap_lv_label_set_text(lv_obj_t *obj, const char *text)
{
    char *copy = display_copy(text);
    __real_lv_label_set_text(obj, copy ? copy : text);
    if (copy) lv_free(copy);
}

void __wrap_lv_label_set_text_static(lv_obj_t *obj, const char *text)
{
    char *copy = display_copy(text);
    if (copy) {
        // The static API retains its input pointer; use the copying API here.
        __real_lv_label_set_text(obj, copy);
        lv_free(copy);
    } else __real_lv_label_set_text_static(obj, text);
}
