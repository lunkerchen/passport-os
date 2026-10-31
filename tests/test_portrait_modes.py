"""Exercise the production renderer's color/monochrome conversion."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'main/apps/home/app_home.cc').read_text()
renderer = source[source.index('void expand_portrait(void)'):source.index('// 无头像时显示占位文字')]
prelude = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include "apps/home/home_portrait.h"
using lv_color32_t = uint32_t;
static constexpr unsigned LV_OPA_COVER=255;
static uint8_t input[HOME_AVATAR_MAX_BYTES],output[HOME_PORTRAIT_I8_BYTES];
static uint8_t *s_portrait_packed=input,*s_portrait_pixels=output;
static int s_portrait_dsc;
static void lv_image_cache_drop(const void*){}
static uint32_t lv_color_hex(uint32_t rgb){return rgb;}
static uint32_t lv_color_to_32(uint32_t rgb,unsigned alpha){return rgb|(alpha<<24);}
static uint32_t ui_theme_portrait_subject_color(unsigned level){const uint32_t values[]={0x103020,0x306040,0x70a080,0xb0e0c0};return values[level];}
'''
checks = r'''
int main(){
 memcpy(input,"PC38",4);input[4]=4;
 for(unsigned i=1;i<256;i++)input[8+i*4+3]=255;
 const uint32_t rgb[]={0,0xffff0000,0xff00ff00,0xff0000ff};
 memcpy(input+8,rgb,sizeof(rgb));input[1032]=1;input[1033]=2;input[1034]=3;
 assert(home_portrait_valid_color(input));
 uint8_t original[sizeof(input)];memcpy(original,input,sizeof(input));
 expand_portrait();assert(!memcmp(output,input+8,sizeof(output)));
 input[5]=1;assert(home_portrait_valid_color(input));expand_portrait();
 const auto *palette=reinterpret_cast<const uint32_t*>(output);
 assert(palette[0]==0);
 assert(palette[1]==(ui_theme_portrait_subject_color(1)|0xff000000));
 assert(palette[2]==(ui_theme_portrait_subject_color(2)|0xff000000));
 assert(palette[3]==(ui_theme_portrait_subject_color(0)|0xff000000));
 assert(!memcmp(output+1024,input+1032,HOME_PORTRAIT_PIXELS));
 assert(!memcmp(input+8,original+8,sizeof(input)-8));
 input[5]=0;expand_portrait();assert(!memcmp(input,original,sizeof(input)));assert(!memcmp(output,input+8,sizeof(output)));
 input[5]=2;assert(!home_portrait_valid_color(input));
}
'''
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'test.cc'
    path.write_text(prelude+renderer+checks)
    binary=path.with_suffix('')
    subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(root/'main'),str(path),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
print('Production portrait renderer: color/monochrome/color roundtrip, matching preview levels, transparency and source preservation PASS')
