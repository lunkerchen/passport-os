# 本 fork 的第三方資源

## 思源黑體 TC

繁體中文字型子集來自 Adobe／Google 的 Source Han Sans（思源黑體）Traditional Chinese Normal。

- 官方專案：https://github.com/adobe-fonts/source-han-sans
- OTF：https://raw.githubusercontent.com/adobe-fonts/source-han-sans/release/OTF/TraditionalChinese/SourceHanSansTC-Normal.otf
- 本次使用 OTF 的 SHA256：`44a94b620f226edafdb675693a9bbeb6f51b050a0c3ca5c64c47be108d5be067`
- 授權：[SIL Open Font License 1.1](licenses/SourceHanSans-LICENSE.txt)
- 產生工具：`lv_font_conv@1.5.3`

本 fork 將字型轉換為 LVGL 使用的 C 子集資料，未改變字形設計。原始 OTF 留在忽略的快取目錄；授權文字隨衍生字型一起保留。

## OpenCC

`main/ui/zh_tw_glyph_map.h` 由 `opencc-python-reimplemented==0.1.7` 的 `s2twp` 單字元映射產生。這個表僅用於畫面顯示副本，不改變原始儲存值、網路查詢條件或服務回覆。

- OpenCC：https://github.com/BYVoid/OpenCC
- Python 實作：https://github.com/yichen0831/opencc-python
- 授權：[Apache License 2.0](licenses/OpenCC-LICENSE.txt)
- 產生工具：`tools/generate_zhtw_glyph_map.py`

固定介面文案另經台灣用語調整，並非全部依賴單字元轉換。

其他上游程式碼、SDK、字型與圖像仍遵循原作者保留的授權與聲明；Muse Jollybot 形象請另見 `main/apps/muse/JOLLYBOT-NOTICE.md`。
