from pathlib import Path
import re, subprocess, json
from opencc import OpenCC
root=Path(__file__).resolve().parents[1]
base=root/'.cache'
base.mkdir(exist_ok=True)
cc=OpenCC('s2twp')
font=root/'.cache/fonts/SourceHanSansTC-Normal.otf'
import hashlib, urllib.request
expected='44a94b620f226edafdb675693a9bbeb6f51b050a0c3ca5c64c47be108d5be067'
if not font.exists():
    font.parent.mkdir(parents=True,exist_ok=True)
    urllib.request.urlretrieve('https://raw.githubusercontent.com/adobe-fonts/source-han-sans/release/OTF/TraditionalChinese/SourceHanSansTC-Normal.otf',font)
if hashlib.sha256(font.read_bytes()).hexdigest()!=expected:
    raise SystemExit('Source Han Sans TC font checksum mismatch')
# Gather displayed literals, excluding logs/comments and generated pixel arrays.
token=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\]|\\.)*"',re.S)
def chars_from_source(paths):
    result=set()
    for p in paths:
        if p.is_file() and p.suffix in {'.c','.cc','.cpp','.h'} and not p.name.endswith(('_frames.c','_font_20.c','_digits_48.c')):
            for m in token.finditer(p.read_text()):
                if m.group().startswith('"'): result.update(c for c in m.group() if ord(c)>126)
    return result
all_chars=chars_from_source([root/'main/boot_splash.c',*root.joinpath('main/apps').rglob('*'),*root.joinpath('main/launcher').rglob('*'),*root.joinpath('main/ui').rglob('*'),*root.joinpath('components/passport_muse').glob('*.cc')])
report={}
for p in [*root.glob('main/fonts/*.c'),root/'main/apps/pomodoro/pomodoro_font_20.c']:
    old=p.read_text(); name=p.stem
    glyphs={chr(int(x,16)) for x in re.findall(r'/\* U\+([A-Fa-f0-9]{4,6})',old)}
    glyphs |= set(cc.convert(''.join(sorted(glyphs))))
    if name in {'buddy_font_16','ui_font_20'}: glyphs |= all_chars
    elif name.startswith('radio_font'): glyphs |= chars_from_source(root.joinpath('main/apps/radio').glob('*'))
    elif name=='voice_font_20': glyphs |= chars_from_source(root.joinpath('main/apps/voice').glob('*'))
    glyphs={c for c in glyphs if ord(c)>126}
    size=int(re.search(r'Size: (\d+)',old)[1]); bpp=int(re.search(r'Bpp: (\d+)',old)[1])
    cmd=['npx','--yes','lv_font_conv@1.5.3','--font',str(font.relative_to(root)),'--range','0x20-0x7e','--symbols',''.join(sorted(glyphs)),'--size',str(size),'--bpp',str(bpp),'--format','lvgl','--no-compress','--no-prefilter','--no-kerning','--lv-include','lvgl.h','--lv-font-name',name,'-o',str(p.relative_to(root))]
    fallback=re.search(r'\.fallback\s*=\s*&([A-Za-z_0-9]+)',old)
    if fallback: cmd += ['--lv-fallback',fallback[1]]
    subprocess.run(cmd,check=True,cwd=root)
    report[name]={'size':size,'bpp':bpp,'non_ascii_glyphs':len(glyphs),'fallback':fallback[1] if fallback else None}
    print(name,len(glyphs),flush=True)
(base/'font-generation.json').write_text(json.dumps(report,indent=2)+'\n')
