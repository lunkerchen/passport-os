"""Exercise real gallery code while an LVGL-like task owns the display."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'main/apps/home/app_home.cc').read_text()
context = source[source.index('constexpr uint16_t kJpegMcuHeight'):source.index('std::size_t share_jpeg_input')]
draw = source[source.index('bool home_show_share_image()'):source.index('void toggle_share_view()')]

code = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <thread>
using std::size_t;
constexpr int HOME_SHARE_PATH_MAX = 512;
constexpr int HOME_SHARE_W = 240, HOME_SHARE_H = 320;
constexpr int ESP_OK = 0;
static uint8_t s_share_index;
static const char *image_path;
static std::timed_mutex display_mutex;
static std::atomic<bool> lvgl_active{false}, overlap{false}, started{false}, dma_pending{false};
static bool reject_jpeg;
[[maybe_unused]] static bool bsp_lvgl_lock(int timeout_ms) {
    return display_mutex.try_lock_for(std::chrono::milliseconds(timeout_ms));
}
[[maybe_unused]] static void bsp_lvgl_unlock() { display_mutex.unlock(); }
[[maybe_unused]] static void vTaskDelay(unsigned ticks) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ticks));
}
#define pdMS_TO_TICKS(ms) (ms)
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGI(...) ((void)0)
struct JDEC { void *device; uint16_t width, height; };
struct JRECT {};
enum JRESULT { JDR_OK, JDR_ERROR };
static bool home_profile_share_path_at(uint8_t, char *path, size_t cap) {
    return std::snprintf(path, cap, "%s", image_path) > 0;
}
static void *bsp_display_io() { return reinterpret_cast<void *>(1); }
static int esp_lcd_panel_io_tx_param(void *, int, const void *, int) {
    if (lvgl_active.load()) overlap.store(true);
    dma_pending.store(false); // the real call waits for outstanding transfers
    return ESP_OK;
}
''' + context + r'''
static size_t share_jpeg_input(JDEC *, uint8_t *, size_t) { return 0; }
static int share_jpeg_output(JDEC *, void *, JRECT *) { return 1; }
static JRESULT jd_prepare(JDEC *d, size_t (*)(JDEC *, uint8_t *, size_t),
                          void *, size_t, void *ctx) {
    d->device = ctx;
    d->width = HOME_SHARE_W;
    d->height = HOME_SHARE_H;
    return reject_jpeg ? JDR_ERROR : JDR_OK;
}
static JRESULT jd_decomp(JDEC *d, int (*)(JDEC *, void *, JRECT *), int) {
    // Model the actual direct JPEG transfer, not merely allocation or setup.
    if (lvgl_active.load() || dma_pending.load()) overlap.store(true);
    static_cast<ShareJpegContext *>(d->device)->color_pending = true;
    dma_pending.store(true);
    return JDR_OK;
}
''' + draw + r'''
int main(int argc, char **argv) {
    assert(argc == 2);
    image_path = argv[1];
    std::thread lvgl([] {
        std::lock_guard<std::timed_mutex> lock(display_mutex);
        lvgl_active.store(true);
        started.store(true);
        std::this_thread::sleep_for(std::chrono::milliseconds(120));
        dma_pending.store(true); // last LVGL transfer can outlive its caller
        lvgl_active.store(false);
    });
    while (!started.load()) std::this_thread::yield();
    assert(home_show_share_image());
    lvgl.join();
    assert(!overlap.load());
    assert(!dma_pending.load());
    // A failed decode must also release ownership for the next update.
    reject_jpeg = true;
    assert(!home_show_share_image());
    assert(display_mutex.try_lock());
    display_mutex.unlock();
    reject_jpeg = false;
    assert(home_show_share_image());
    std::puts("Gallery display: JPEG and LVGL cannot use the display concurrently; failure releases ownership: PASS");
}
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    harness = tmp / 'share_display.cpp'
    image = tmp / 'card.jpg'
    image.write_bytes(b'fixture')
    harness.write_text(code)
    exe = tmp / 'share_display'
    subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                    '-fsanitize=address,undefined', str(harness), '-o', str(exe)], check=True)
    subprocess.run([str(exe), str(image)], check=True)
