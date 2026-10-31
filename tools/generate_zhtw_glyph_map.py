"""Regenerate the display-only Simplified-to-Traditional CJK mapping table."""
from pathlib import Path
from opencc import OpenCC

root = Path(__file__).resolve().parents[1]
converter = OpenCC('s2twp')
pairs = []
for codepoint in range(0x3400, 0xA000):
    original = chr(codepoint)
    translated = converter.convert(original)
    if len(translated) == 1 and translated != original and 0x800 <= ord(translated) <= 0xFFFF:
        pairs.append((codepoint, ord(translated)))
output = root / 'main/ui/zh_tw_glyph_map.h'
output.write_text(
    '// OpenCC s2twp one-character display mappings; sorted by source code point.\n'
    'static const uint16_t zh_tw_map[][2] = {\n'
    + ''.join(f'    {{0x{a:04x}, 0x{b:04x}}},\n' for a, b in pairs)
    + '};\n'
)
print(f'Generated {len(pairs)} display mappings')
