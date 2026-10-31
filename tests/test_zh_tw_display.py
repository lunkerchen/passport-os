from pathlib import Path
import subprocess, tempfile
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='passport-zhtw-') as tmp:
    work=Path(tmp)
    (work/'lvgl.h').write_text('''#include <stdlib.h>
typedef struct { int unused; } lv_obj_t;
extern int fail_alloc;
static inline void *lv_malloc(size_t n) { return fail_alloc ? NULL : malloc(n); }
static inline void lv_free(void *p) { free(p); }
''')
    (work/'test.c').write_text('''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lvgl.h"
int fail_alloc;
static char rendered[1024];
static const char *static_pointer;
void __real_lv_label_set_text(lv_obj_t *o, const char *s) { (void)o; if (s) strcpy(rendered,s); else strcpy(rendered,"<refresh>"); }
void __real_lv_label_set_text_static(lv_obj_t *o, const char *s) { (void)o; static_pointer=s; }
void __wrap_lv_label_set_text(lv_obj_t *,const char *);
void __wrap_lv_label_set_text_static(lv_obj_t *,const char *);
int main(void) {
    lv_obj_t label={0};
    const char source[]="网络连接 · 广州电台 · USB Wi-Fi 123 😀";
    __wrap_lv_label_set_text(&label,source);
    assert(!strcmp(rendered,"網絡連接 · 廣州電臺 · USB Wi-Fi 123 😀"));
    assert(!strcmp(source,"网络连接 · 广州电台 · USB Wi-Fi 123 😀"));
    __wrap_lv_label_set_text_static(&label,"设置完成");
    assert(!strcmp(rendered,"設置完成"));
    const char *literal="繁體中文 Wi-Fi";
    __wrap_lv_label_set_text_static(&label,literal);
    assert(static_pointer==literal);
    __wrap_lv_label_set_text(&label,NULL);
    assert(!strcmp(rendered,"<refresh>"));
    __wrap_lv_label_set_text(&label,""); assert(!*rendered);
    const char short_utf8[]={ (char)0xe4, (char)0xb8, 0 };
    __wrap_lv_label_set_text(&label,short_utf8); assert(!strcmp(rendered,short_utf8));
    fail_alloc=1;
    __wrap_lv_label_set_text(&label,"连接"); assert(!strcmp(rendered,"连接"));
    fail_alloc=0;
    for(int i=0;i<1000;i++) __wrap_lv_label_set_text(&label,source);
    puts("Traditional Chinese rendering: UTF-8, source preservation, static lifetime, NULL, allocation failure and 1000 updates PASS");
}
''')
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I'+str(work),'-I'+str(root/'main/ui'),str(root/'main/ui/zh_tw_display.c'),str(work/'test.c'),'-o',str(work/'test')],check=True)
    subprocess.run([str(work/'test')],check=True)
