# cn-epub-maker

將中文小說 TXT 轉換成 EPUB 的 Python 工具。適合把整理過的中文小說文字轉成可閱讀的 EPUB，也提供可選的 Intermediate JSON 供檢查與除錯。

## 安裝

需要：

- Python 3.10 以上
- Pandoc，且 `pandoc` 必須能在 `PATH` 中執行
- EPUBCheck（選用）：安裝後 `validate` 會額外執行 EPUB 標準驗證

建議使用虛擬環境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

確認安裝：

```bash
pandoc --version
novel-epub --help
```

也可以使用 module 方式執行：

```bash
python3 -m novel_epub.cli --help
```

## 基本使用

最基本的 build 需要 TXT、書名與作者：

```bash
novel-epub build novel.txt --title "書名" --author "作者"
```

預設輸出檔名為 `<書名>_<作者>.epub`。指定輸出位置：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --output book.epub
```

## 常用選項

| 需求 | 參數 | 說明 |
|---|---|---|
| 指定輸出 | `--output` | 指定 EPUB 輸出檔案 |
| 指定來源編碼 | `--encoding` | 例如 `utf-8`、`gb18030`、`gbk`、`big5` |
| 一行一段 | `--paragraph-mode line` | 適合「每個來源行就是一個段落」的 TXT |
| 保留原本段落包裝 | `--paragraph-mode wrapped` | 預設；連續非空白行視為同一段落 |
| 不做簡繁轉換 | `--no-opencc` | 停用預設的 OpenCC 轉換 |
| 不做標點轉換 | `--no-punctuation` | 停用標點轉換 |
| 加入封面 | `--cover` | 指定封面圖片 |
| 指定 EPUB 語言 | `--lang` | 預設為 `zh-TW` |
| 保留 Intermediate | `--keep-intermediate` | 將 build 過程的 JSON 資料寫到磁碟 |
| 停用內容 transformation | `--full-source` | 保留來源內容，不做 OpenCC、標點與 junk cleaning |

### 來源編碼

程式會自動嘗試常見中文編碼。若知道來源編碼，建議直接指定，例如：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding gb18030
```

目前常見選項包括 `utf-8-sig`、`utf-8`、`gb18030`、`gbk`、`big5`。Normalize 也會處理 UTF-8 BOM 與不同 newline 表示。

### 段落模式

預設使用 `wrapped`：連續的非空白來源行視為同一個邏輯段落，空白行才結束段落。

如果來源 TXT 是「一行就是一個段落」，使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --paragraph-mode line
```

兩種模式都不會因空白行產生空的段落。段落模式也不會改變章節、卷與番外標題的辨識規則。

## 文字處理

一般 build 會依序處理來源文字：

```text
Normalize
  ↓
Junk Cleaning
  ↓
OpenCC
  ↓
Punctuation Conversion
  ↓
Parser
  ↓
EPUB
  ↓
Validation
```

OpenCC 預設將內容轉為繁體中文，可用 `--no-opencc` 停用。

標點轉換預設啟用，可用 `--no-punctuation` 停用。

### Junk Cleaner

Junk Cleaner 只負責「移除可以明確判定為非正文的內容」，不負責一般文字替換。預設不會自行套用一組可能誤刪小說內容的規則。

規則使用 `JunkRule` 表示，核心欄位為：

- `target`：`line` 或 `block`
- `matcher`：`exact`、`contains` 或 `regex`
- `pattern`：匹配文字或正則表達式

例如：

```text
line:exact:本章節完
line:contains:請收藏本書
line:regex:^本章由.*整理$
```

`line` 逐行判斷；`block` 則以空白行分隔的連續非空白行為單位，因此應更謹慎使用。

JunkRule 的完整設定格式與規則語義見 [`docs/junk-rule-configuration.md`](docs/junk-rule-configuration.md)。目前 README 只描述規則模型，不把尚未整合完成的設定檔或 CLI 載入方式當成已可用功能。

## Full Source Mode

如果希望停用內容 transformation，可以使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --full-source
```

此模式仍會執行 Normalize，因此不是 byte-for-byte 的原始檔複製；它的目的是保留來源文字內容，同時仍進行必要的輸入正規化。

## 封面與語言

加入封面：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --cover cover.jpg
```

指定語言：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --lang zh-TW
```

預設 EPUB 語言為 `zh-TW`。

## Intermediate

Intermediate 是可選的 build 輸出，主要用來檢查 Parser 結果與 transformation audit，不是一般使用者必須操作的格式。

啟用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate
```

預設會建立 `<輸入檔名>.intermediate/`；也可以指定位置：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate \
  --intermediate book.intermediate
```

輸出大致如下：

```text
novel.intermediate/
├── book.json
├── preamble.json          # 有前言時才會產生
└── chapters/
    ├── 000001.json
    ├── 000002.json
    └── ...
```

Intermediate 是序列化的 build 結果，方便人為檢查與除錯；目前沒有承諾可以由 Intermediate 完整反向重建執行時的 `Book`。

## 驗證 EPUB

`build` 完成後會執行內建 EPUB 結構驗證。也可以單獨驗證既有 EPUB：

```bash
novel-epub validate book.epub
```

若系統中存在 EPUBCheck，`validate` 會再執行外部 EPUB 標準驗證；沒有安裝時，內建驗證仍可使用。

## 常見問題

### 找不到 Pandoc

先確認：

```bash
pandoc --version
```

如果指令不存在，請安裝 Pandoc，並確認它位於 `PATH`。

### 中文顯示錯誤

如果 TXT 使用 Big5、GBK 或 GB18030，請明確指定來源編碼：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding big5
```

### 不想轉換簡繁

使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --no-opencc
```

### 不想轉換標點

使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --no-punctuation
```

### 想保留來源文字，不做內容轉換

使用 `--full-source`。注意它仍會進行 Normalize，所以不是 byte-for-byte 複製。

## 架構與詳細文件

一般使用不需要理解內部架構。需要了解行為規格或進行開發時，可從以下文件開始：

- [`docs/architecture-overview.md`](docs/architecture-overview.md) — 整體架構
- [`docs/physical-document-and-formatting-contract.md`](docs/physical-document-and-formatting-contract.md) — TXT 來源與格式語義
- [`docs/junk-rule-configuration.md`](docs/junk-rule-configuration.md) — JunkRule 設定契約
- [`docs/real-reader-acceptance-matrix.md`](docs/real-reader-acceptance-matrix.md) — EPUB 閱讀器驗收情境
