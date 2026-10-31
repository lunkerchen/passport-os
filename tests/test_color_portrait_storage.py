"""Run production portrait storage code on a temporary host filesystem."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=(root/'main/apps/home/home_profile.c').read_text()
body=source[source.index('static esp_err_t avatar_load(void)'):source.index('static bool card_path(')]
prelude=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include "apps/home/home_portrait.h"
typedef int esp_err_t;
typedef int nvs_handle_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG -2
#define ESP_ERR_INVALID_SIZE -3
#define ESP_ERR_NOT_FOUND -4
#define ESP_ERR_NVS_NOT_FOUND -5
#define ESP_ERR_NO_MEM -6
#define ESP_ERR_INVALID_STATE -7
#define NVS_READONLY 0
#define NVS_READWRITE 1
#define NVS_NAMESPACE "home"
#define AVATAR_PATH "legacy.bin"
#define ESP_LOGW(...) ((void)0)
#define ESP_LOGI(...) ((void)0)
#define portENTER_CRITICAL(x) ((void)0)
#define portEXIT_CRITICAL(x) ((void)0)
static const char *s_avatar_paths[]={"a.bin","b.bin"};
static bool s_avatar_loaded=true;
static int s_avatar_bank=-1,s_avatar_upload_bank;
static FILE *s_avatar_stream;
static size_t s_avatar_written,s_avatar_expected;
static unsigned s_version;
static bool storage_busy(void){return false;}
static int ensure_spiffs(void){return ESP_OK;}
static int nvs_open(const char *ns,int mode,int *h){(void)ns;(void)mode;*h=1;return 0;}
static int nvs_get_str(int h,const char *key,char *out,size_t *n){(void)h;(void)key;(void)out;(void)n;return ESP_ERR_NOT_FOUND;}
static int nvs_set_str(int h,const char *key,const char *v){(void)h;assert(!strcmp(key,"portrait_v2"));assert(*v=='a'||*v=='b');return 0;}
static int nvs_commit(int h){(void)h;return 0;}
static void nvs_close(int h){(void)h;}
static const char *esp_err_to_name(int e){(void)e;return "error";}
'''
tests=r'''
int main(void){
 uint8_t mono[HOME_AVATAR_BYTES],color[HOME_AVATAR_COLOR_BYTES],out[HOME_AVATAR_MAX_BYTES];
 memset(mono,0xff,sizeof(mono));home_portrait_init_header(mono,3);
 assert(home_profile_write_avatar_chunk(mono,sizeof(mono),true,true,sizeof(mono))==ESP_OK);
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&!memcmp(out,mono,sizeof(mono)));
 int bank=s_avatar_bank;
 memset(color,0,sizeof(color));memcpy(color,"PC38",4);color[4]=4;
 for(int i=1;i<256;i++)color[8+i*4+3]=255;
 color[8+4+2]=255;memset(color+1032,1,HOME_PORTRAIT_PIXELS);
 assert(home_portrait_valid_color(color));
 assert(home_profile_write_avatar_chunk(color,512,true,false,sizeof(color))==ESP_OK);
 assert(home_profile_has_avatar());assert(s_avatar_bank==bank);
 assert(home_profile_write_avatar_chunk(color+512,sizeof(color)-512,false,true,sizeof(color))==ESP_OK);
 assert(s_avatar_bank!=bank);
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&!memcmp(out,color,sizeof(color)));
 assert(home_profile_read_avatar(out,HOME_AVATAR_BYTES)==ESP_ERR_INVALID_SIZE);
 color[5]=1;assert(home_portrait_valid_color(color));
 assert(home_profile_write_avatar_chunk(color,sizeof(color),true,true,sizeof(color))==ESP_OK);
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&out[5]==1&&!memcmp(out,color,sizeof(color)));
 bank=s_avatar_bank;color[5]=2;
 assert(home_profile_write_avatar_chunk(color,sizeof(color),true,true,sizeof(color))==ESP_ERR_INVALID_ARG);
 assert(s_avatar_bank==bank);color[5]=1;
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&!memcmp(out,color,sizeof(color)));
 color[5]=0;assert(home_profile_write_avatar_chunk(color,sizeof(color),true,true,sizeof(color))==ESP_OK);
 bank=s_avatar_bank;color[11]=255;
 assert(home_profile_write_avatar_chunk(color,sizeof(color),true,true,sizeof(color))==ESP_ERR_INVALID_ARG);
 assert(s_avatar_bank==bank);color[11]=0;
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&!memcmp(out,color,sizeof(color)));
 color[0]='X';assert(home_profile_write_avatar_chunk(color,sizeof(color),true,true,sizeof(color))==ESP_ERR_INVALID_ARG);
 assert(s_avatar_bank==bank);
 assert(home_profile_write_avatar_chunk(mono,sizeof(mono),true,true,sizeof(mono))==ESP_OK);
 assert(home_profile_read_avatar(out,sizeof(out))==ESP_OK&&!memcmp(out,mono,sizeof(mono)));
 assert(home_portrait_stored_size(out)==HOME_AVATAR_BYTES);
 puts("Color portrait storage: atomic bank commit, legacy roundtrip, color roundtrip, short buffer and corrupt header/palette rollback: PASS");
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'test.c';p.write_text(prelude+body+tests)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-fsanitize=address,undefined','-I'+str(root/'main'),str(p),'-o',str(Path(temp)/'test')],check=True)
 subprocess.run([str(Path(temp)/'test')],cwd=temp,check=True)
