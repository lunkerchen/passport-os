# 開發與驗證

[文件目錄](index.md) · [安裝與分割區](INSTALL.zh-TW.md) · [第三方資源](THIRD-PARTY-zh-TW.md)

本 fork 以 Passport OS `0.2.0-rc.56` 為基礎，版本字串是 `0.2.0-rc.56-tw-scroll`。建置使用 **ESP-IDF 5.5.3**；不要因其他 ESP32 專案改用新版 SDK，就直接替換這個專案的依賴。

## 程式入口與目錄

| 路徑 | 用途 |
| --- | --- |
| [main/main.cc](../main/main.cc) | 裝置啟動、輸入事件與診斷命令 |
| [main/launcher](../main/launcher) | 應用程式註冊、選單、系統設定與連網入口 |
| [main/apps/home](../main/apps/home) | 首頁、個人資料、頭像／名片儲存及手機設定頁 |
| [main/apps/radio](../main/apps/radio) | 電臺清單、播放器、HLS 及收音機畫面 |
| [main/ui](../main/ui) | 共用介面、主題及顯示字串轉換 |
| [main/fonts](../main/fonts) | 已生成的 LVGL 字型子集 |
| [components/bsp](../components/bsp) | 音訊、按鍵、螢幕與電池等板級介面 |
| [components/passport_muse](../components/passport_muse) | Muse 服務整合 |
| [tests](../tests) | 主機端功能與錯誤路徑測試 |
| [tools](../tools) | 建置驗證、資源生成與發布工具 |

韌體選單由註冊表決定。增加應用程式時，需同時核對註冊、生命週期、輸入事件、資源釋放、字型與記憶體預算，不能只新增一張畫面。

## 公開建置

```bash
IDF_DIR=/path/to/esp-idf bash build.sh release
```

這條路徑重新從 `sdkconfig.defaults` 產生設定，使用 `PASSPORT_PUBLIC_RELEASE=ON`，清空預設個人代理設定，並以 `PASSPORT_MUSE_USE_JOLLYBOT=ON` 建置。`IDF_DIR` 指向已安裝好工具鏈的 ESP-IDF 5.5.3 目錄。

成功時 `tools/verify_firmware.py` 檢查開機程式、分割區、應用程式大小、靜態 SRAM 預算、公開預設值與合併鏡像。不能為了讓超出預算的修改通過，就直接調高限制。

已啟用 ESP-IDF 環境後，也可使用上游驗證入口：

```bash
bash tools/validate.sh --firmware
```

該指令會用暫存建置目錄重建，並把完整鏡像保存到 `build/`。它與 `build.sh release` 的輸出目錄不同，交付時要寫清楚實際使用哪個檔案。

## 修改電臺清單

編輯 [radio_presets.h](../main/apps/radio/radio_presets.h)。本版正常清單包含十筆 `RadioStation`，欄位為名稱、描述、串流網址及頻率資訊。名稱與描述使用 UTF-8，容量以位元組計算。

- 名稱陣列 64 bytes、描述 96 bytes、網址 256 bytes，均需留結尾零字元。
- 播放器上限為十臺，已有編譯期檢查避免清單超過預留工作區。
- `kRadioFixedCatalog=true` 使正常流程保留固定清單，不執行城市搜尋覆蓋。
- `PASSPORT_RADIO_HLS_TEST` 是既有測試清單分支，不應誤當成正常使用版本。
- 頻率欄位為 0 時，刻度按清單位置分布；畫面數字不代表已量測到真正 FM 頻率。

先確認公開入口能取得實際音訊，不只檢查 HTTP 200。避免保存會到期的重新導向 Token 網址。電腦可解碼仍不能取代 ESP32 實機測試，因為 TLS、記憶體與解碼器限制可能不同。

本次實測修正兩項差異：臺北廣播電臺的 HLS 純音訊變體約 323 kbit/s，解析器上限調為 384 kbit/s；警廣改用官方串流主機的公開 HTTP 1935 入口，避免 HTTPS 音訊片段的 TLS 讀取錯誤。解析器仍拒絕影片、超過位元率上限，以及不支援的加密／分段格式。

## 繁中字型與顯示轉換

介面固定文案已改為繁體中文與台灣用語。動態文字由 [zh_tw_display.c](../main/ui/zh_tw_display.c) 在 LVGL 顯示入口轉換副本，保留原始網路名稱、服務查詢參數、伺服器回覆與儲存內容。

單字元轉換表來自 OpenCC `s2twp`，只涵蓋這份表的 CJK 映射，不等同完整語意翻譯。字型同樣是子集，使用者輸入任意罕用字時仍可能缺字。

一般建置使用追蹤的 C 字型檔，不需要重新下載原字型。更改中文文案或轉換規則後，準備 Node.js／npm 與 `uv`：

```bash
uv run --with opencc-python-reimplemented==0.1.7 python tools/generate_zhtw_glyph_map.py
uv run --with opencc-python-reimplemented==0.1.7 python tools/generate_zhtw_fonts.py
```

第二條命令下載思源黑體 TC 到忽略的 `.cache/fonts/`，驗證 SHA256，再用 `lv_font_conv@1.5.3` 產生字型。生成工具保留既有字元和必要回退字型；原字型校驗不符時會停止。來源與授權見[第三方資源說明](THIRD-PARTY-zh-TW.md)。

## 彩色頭像格式與儲存

[home_portrait.h](../main/apps/home/home_portrait.h) 定義格式及驗證：

| 格式 | 用途 |
| --- | --- |
| 舊 1bpp／2bpp | 讀取舊版單色人像 |
| `PT35` | 預設模式、2bpp 亮度與獨立可見遮罩 |
| `PC38` | 8-byte 標頭、256 筆 BGRA 調色盤、96 × 138 個 8-bit 色彩索引 |

`PC38` 調色盤索引 0 透明，1–255 為不透明色彩，總長度為 **14,280 bytes**。標頭 byte 5 保存顯示方式：0 為彩色，1 為主題單色。兩種模式都保留同一份原始 BGRA 調色盤與色彩索引，單色只轉換首頁顯示副本。

手機設定頁會讀取既有頭像，以相同亮度公式預覽單色效果。只有完成儲存才寫回顯示標記；讀取失敗不應改寫原頭像，較晚回傳的舊資料也不能覆蓋使用者剛選的新照片。舊版韌體不接受 byte 5 為 1 的格式，降級前應先切回彩色並儲存。

上傳串流寫入非現用的 a／b 檔案，完成長度與標頭／調色盤驗證後，才提交 NVS 指標。中斷或驗證失敗不能讓未完成檔案取代目前頭像。修改格式時，同時更新上傳處理、讀取容量、首頁配置／釋放及舊格式相容測試。

個人簽名、照片或 Wi-Fi 密碼不是建置設定；不要硬編碼進程式來達成個人化。

## 首頁簽名跑馬燈

首頁簽名使用 LVGL 原生 `LV_LABEL_LONG_MODE_SCROLL_CIRCULAR`，以每秒約 28 像素的速度循環捲動。捲動依文字量測寬度觸發，不按字元數硬切；短文字由 LVGL 維持靜止。沒有新增文字副本緩衝或常駐工作執行緒，生命週期跟隨首頁標籤。

實機驗證比較同一簽名區域在不同時間的截圖：長文字位置改變、短文字畫面不變，並切換首頁／設定三次後檢查記憶體完整性及原個人資料回復。結果見[本版摘要](verification-tw-scroll.json)。

## 執行測試

以下指令從專案根目錄執行，使用 Python 3、Node.js 與可用的 C／C++ 編譯器。文件以 `python3` 為例；Windows 請換成對應 Python 3 入口，或使用符合主機測試環境的 WSL。

```bash
python3 tools/check_repo.py --firmware-fork
python3 tests/test_zh_tw_display.py
node tests/test_portrait_pixels.js
node tests/test_portrait_mode_page.js
python3 tests/test_portrait_modes.py
python3 tests/test_color_portrait_storage.py
python3 tests/test_avatar_upload.py
python3 tests/test_home_portrait_lifecycle.py
python3 tests/test_radio_source.py
c++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -Imain tests/test_radio_hls.cc -o /tmp/passport-radio-hls
/tmp/passport-radio-hls
```

| 測試 | 主要證據 |
| --- | --- |
| `test_zh_tw_display.py` | UTF-8、來源不變、靜態字串生命週期、空值與配置失敗 |
| `test_portrait_pixels.js` | 色彩保留、透明度、調色盤容量、單色／彩色切換與舊圖預覽 |
| `test_portrait_mode_page.js` | 不重新選檔的儲存／讀回流程、失敗保留與延遲回應保護 |
| `test_portrait_modes.py` | 實際首頁繪圖函式的色彩往返、預覽亮度一致性與來源保留 |
| `test_color_portrait_storage.py` | 原子提交、舊格式／彩色往返、短緩衝與毀損資料回復 |
| `test_avatar_upload.py` | 分段上傳、暫時逾時、斷線、認證與儲存失敗 |
| `test_home_portrait_lifecycle.py` | 配置失敗、格式切換、快取與記憶體釋放 |
| `test_radio_source.py` | HLS 重新導向、分段、刷新、取消、清理與錯誤回應 |
| `test_radio_hls.cc` | 滑動視窗、音訊變體、較高位元率與影片拒絕 |

這份清單是針對本 fork 變更的檢查，不取代所有上游測試。上游 `tools/test-host.sh` 在 macOS Clang 有既有 `-Wnon-c-typedef-for-linkage` 錯誤，部分連結指令也使用 Linux 專用選項；因此本版沒有宣稱 macOS 上的完整套件通過。Linux／CI 應依其實際輸出判定，不把本機摘要當成 GitHub Actions 綠燈。

另可執行瀏覽器流程測試（需要 Playwright 及 Chromium，macOS 已有 Google Chrome 時會優先使用它）：

```bash
uv run --with playwright playwright install chromium
uv run --with playwright python tests/test_portrait_mode_browser.py
```

這項測試以模擬裝置 API 操作實際手機頁面，驗證未選擇新照片時的切換、儲存、重新開頁及舊圖限制，不會操作實際裝置。

## 實機驗證與發布紀錄

[verification-tw-portrait.json](verification-tw-portrait.json) 記錄本版建置、主機／瀏覽器流程及實機模式切換結果，包含重開機後保留選擇與原始資料往返。[verification-tw-radio.json](verification-tw-radio.json) 保留前版十臺實機解碼結果；兩份摘要各自對應已驗證的功能與鏡像。

- 收音機：需在裝置上解碼並把 PCM 送入音訊輸出；電腦能讀到網址只算前置檢查。
- 彩色頭像：以實機畫面 RGB 色塊確認沒有主題染色，並驗證原頭像／個人資料保留。
- 隨身語音：需要使用者實際說話出字，診斷通過或模擬測試不等同端到端完成。
- 記憶體：記錄實際完整性檢查結果，不只看靜態編譯成功。

更新韌體版本時，一併核對 `CMakeLists.txt`、主要 README、[版本紀錄](../CHANGELOG.md)與新的驗證摘要。不要沿用舊版驗證檔來聲稱新版測試完成；新增摘要時保留歷史紀錄。

分享 `.bin` 前，使用公開建置流程並保留 SHA256、硬體條件與分割區說明。個人完整 Flash 備份、原始日誌、帳號憑證和照片不放進發行套件。
