# 備份、建置、安裝與回復

[文件目錄](index.md) · [日常操作](USAGE.zh-TW.md) · [疑難排解](TROUBLESHOOTING.zh-TW.md)

本指南對應 `0.2.0-rc.56-tw-best989`。適用 FoloToy AI Passport、ESP32-C3、8 MB Flash。若裝置已能使用目前版本，不需要為了換照片、改簽名或使用隨身語音再刷機。

## 先判斷要走哪一條路

| 狀況 | 做法 |
| --- | --- |
| 已安裝這版，只想改資料或彩色頭像 | 使用裝置「手機設定」，見[操作指南](USAGE.zh-TW.md) |
| 已安裝相同分割區配置的 Passport OS，要更新程式 | 完整備份、比對分割區，再只寫應用程式 |
| 第一次安裝，或原本是其他韌體 | 完整備份、確認硬體與資料移轉需求，再使用完整鏡像 |
| 不確定硬體、Flash 大小或分割區是否相同 | 先讀取晶片與分割區資料，不直接寫入 |

這份 fork 目前以原始碼發布，沒有承諾可直接下載的預先建置套件。GitHub 的 Source code ZIP 只是原始碼；從原作者 Releases 下載的另一個版本，也不一定含繁中、彩色頭像及臺北清單。

## 工具與序列埠

- 可傳資料的 USB 線，裝置接到電腦後可被辨識。
- 建置需要 Git、ESP-IDF **5.5.3** 與 ESP32-C3 工具鏈。
- 下方讀寫範例使用 `uv` 執行 `esptool==5.6.0`。沒有 `uv` 時，可在獨立 Python 環境安裝相同版本，將命令開頭換成 `python -m esptool`。
- 建置指令使用 Bash。Windows 可在 WSL 建置，再把 `.bin` 複製到 Windows，以 PowerShell 能存取的 COM 埠燒錄；USB 不會自動出現在 WSL。

ESP-IDF 取得方式見 [v5.5.3](https://github.com/espressif/esp-idf/releases/tag/v5.5.3)，`uv` 見[官方安裝說明](https://docs.astral.sh/uv/getting-started/installation/)。不同 SDK 主版本不能直接視為可互換。

查詢序列埠：

```bash
uv run --with pyserial python -m serial.tools.list_ports
```

macOS 常見名稱為 `/dev/cu.usbmodem…`，Windows 常見為 `COM3`，Linux 常見為 `/dev/ttyACM0`。以下的 `YOUR_SERIAL_PORT` 都要換成這次實際查到的名稱，不能照抄其他裝置的埠號。先關閉會占用該埠的序列監看器。

確認晶片：

```bash
uvx --from esptool==5.6.0 esptool --port YOUR_SERIAL_PORT chip-id
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT flash-id
```

應辨識為 ESP32-C3，實體 Flash 為 8 MB。`chip-id` 對 ESP32-C3 可能顯示沒有獨立 chip ID、改讀 MAC；這不等同連線失敗。讀寫動作可能重置裝置，不要在正在輸入語音或傳送資料時執行。

## 先完整備份

把備份放在本機安全位置，檔名換成自己的日期，避免覆蓋既有備份：

```bash
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT --baud 460800 read-flash 0x0 0x800000 passport-backup-YYYYMMDD.bin
```

完成後檔案應為 **8,388,608 bytes**。保存 SHA256：

```bash
uv run python -c "from pathlib import Path; import hashlib; p=Path('passport-backup-YYYYMMDD.bin'); assert p.stat().st_size == 8388608; print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

這份檔案可能含 Wi-Fi 密碼、帳號憑證、身分資料與照片，不要上傳到 GitHub 或公開問題討論。備份也不是可分發的公開韌體。

## 從原始碼建置

```bash
git clone https://github.com/lunkerchen/passport-os.git
cd passport-os
IDF_DIR=/path/to/esp-idf bash build.sh release
```

`/path/to/esp-idf` 指向已安裝好工具鏈的 ESP-IDF 5.5.3 目錄，該目錄須含 `export.sh`。腳本會載入 SDK，從追蹤的 `sdkconfig.defaults` 產生公開建置，使用 ESP32-C3 目標及 Jollybot 圖像。第三方元件由 Component Manager 取得。

成功時應看到韌體佈局、SRAM 預算及公開預設值檢查通過，得到：

| 檔案 | 用途 | 寫入位址 |
| --- | --- | --- |
| `build-public/passport-os.bin` | 應用程式鏡像，相同分割區升級 | `0x10000` |
| `build-public/FoloToy-AI-Passport-full.bin` | 包含開機程式、分割區表與應用程式的完整鏡像 | `0x0` |
| `build-public/partition_table/partition-table.bin` | 核對裝置的分割區表 | 不單獨當作一般升級檔寫入 |

一般建置直接使用已提交的 C 字型，不必先安裝字型產生工具。修改中文文案後才需要[重新產生字型](DEVELOPMENT.zh-TW.md#繁中字型與顯示轉換)。

## 相同分割區的保留資料升級

先讀出裝置分割區表：

```bash
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT read-flash 0x8000 0xc00 device-partitions.bin
```

在專案根目錄與建置結果逐位元組比對：

```bash
uv run python -c "from pathlib import Path; a=Path('device-partitions.bin').read_bytes(); b=Path('build-public/partition_table/partition-table.bin').read_bytes(); assert a == b, 'Partition tables differ: stop the app-only upgrade'; print('Partition table match: PASS')"
```

必須確認備份完成、硬體正確、比對通過，才只寫應用程式：

```bash
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT --baud 460800 write-flash 0x10000 build-public/passport-os.bin
```

這條命令不重寫開機程式、分割區表、NVS 或圖片 storage。**相同分割區不代表任意版本的資料格式都相容**；此版已有測試覆蓋原有頭像格式，若移轉其他分支或較新版本，還要核對其版本說明。

若比對不符，先停止，不要為了讓命令通過而直接改寫分割區表或整片清除。

若要降級到 `0.2.0-rc.56-tw-radio` 或更早版本，請先把本版儲存的彩色照片切回「彩色」並儲存，或使用降級前的完整備份。舊版不認得本版新增的單色顯示標記，可能拒絕顯示該頭像，但這不代表原始色彩資料已刪除。

## 首次完整安裝或切換其他韌體

完整鏡像從 `0x0` 寫入，會覆蓋鏡像範圍內的舊設定。此流程不是「保留資料升級」。確認已備份且接受重新設定後才使用：

```bash
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT --baud 460800 write-flash 0x0 build-public/FoloToy-AI-Passport-full.bin
```

一般安裝不需要先執行整片 `erase-flash`。完整鏡像不是 8 MB 的個人備份，也不保證清掉寫入範圍以外的舊圖片或資料。從其他韌體移轉時，資料能否沿用須另行核對。

此版分割區固定如下，來源為 [partitions.csv](../partitions.csv)：

| 分割區 | 起點 | 大小 | 內容 |
| --- | --- | --- | --- |
| nvs | `0x9000` | `0x6000` | 設定與憑證 |
| phy_init | `0xF000` | `0x1000` | 無線參數 |
| factory | `0x10000` | `0x400000` | 4 MB 應用程式 |
| cardid | `0x410000` | `0x4000` | 裝置身分區域 |
| storage | `0x420000` | `0x200000` | 頭像及名片圖片 |

專案驗證工具另外保護 `0x700000–0x7FFFFF` 的 recovery 實體區域；它目前沒有列在 CSV 的分割區項目中。不要把這些位址拿去套用其他板子或分割區配置。

## 寫入後檢查

1. 確認 esptool 顯示寫入成功及資料雜湊驗證完成，裝置能正常重新開機。
2. 已有設定的裝置應回到首頁；全新設定依畫面進入手機連網流程。
3. 檢查姓名、簽名、頭像和名片是否符合升級前狀態。
4. 開啟收音機，確認清單為十臺，且 Wi-Fi 就緒後能開始播放。
5. 要使用彩色頭像，重新上傳原始彩色照片；舊單色圖不會自動恢復原色。

下載或傳送 `.bin` 後，可用 SHA256 確認檔案沒有變動。自行重建可能因建置時間與環境而得到不同的鏡像雜湊；不能只因它不同於歷史驗證摘要就判定損壞。

## 從自己的完整備份回復

只使用**這台裝置自己、確認完整的 8 MB 備份**。回復會把整台裝置的程式與設定退回備份當時，覆蓋後來新增的資料；需要保留目前狀態時先另做一份新備份。

```bash
uvx --from esptool==5.6.0 esptool --chip esp32c3 --port YOUR_SERIAL_PORT --baud 460800 write-flash 0x0 passport-backup-YYYYMMDD.bin
```

不要使用其他人的完整備份，也不要把公開完整鏡像誤當成自己的還原檔。若裝置無法連線，先看[USB 與燒錄排解](TROUBLESHOOTING.zh-TW.md#usb-與燒錄)。
