# cn-epub-maker

將中文小說 TXT 轉換成 EPUB 的 Python 工具。適合希望把整理過的中文小說文字轉成可閱讀 EPUB 的使用者，也提供 Intermediate JSON 供後續處理與除錯。

## 安裝

需要：

- Python 3.10 以上
- Pandoc，且 `pandoc` 必須能在 `PATH` 中執行
- EPUBCheck 為選用工具；若安裝並放在 `PATH` 中，`validate` 會額外執行 EPUB 標準驗證

建議在虛擬環境中安裝：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

確認 Pandoc：

```bash
pandoc --version
```

確認 CLI：

```bash
novel-epub --help
```

如果不使用安裝後的 `novel-epub` 指令，也可以使用 Python module 方式：

```bash
python3 -m novel_epub.cli --help
```

## 基本使用

最基本的 build 需要輸入 TXT、書名與作者：

```bash
novel-epub build novel.txt --title "書名" --author "作者"
```

預設輸出檔名為 `<書名>_<作者>.epub`。如果需要指定輸出位置：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --output book.epub
```

也可以使用 module 方式執行相同命令：

```bash
python3 -m novel_epub.cli build novel.txt \
  --title "書名" \
  --author "作者" \
  --output book.epub
```

## 來源編碼

程式會自動嘗試常見中文編碼。若知道來源編碼，建議直接指定：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding gb18030
```

目前可指定的常見選項包括 `utf-8-sig`、`utf-8`、`gb18030`、`gbk`、`big5`。Normalize 會處理 UTF-8 BOM 與不同 newline 表示。

## V2 文字處理

一般 build 預設會依序執行：

```text
Normalize
  ↓
Junk Cleaner
  ↓
OpenCC
  ↓
Punctuation Conversion
  ↓
Parser
  ↓
Intermediate
  ↓
EPUB
  ↓
Validation
```

OpenCC 預設啟用，預設 profile 為 `s2twp`：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --opencc-profile s2twp
```

目前也提供 `s2t` profile。可以用 `--no-opencc` 停用 OpenCC：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --no-opencc
```

Punctuation Conversion 預設啟用，可以用 `--no-punctuation` 停用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --no-punctuation
```

Junk Cleaner 是 V2 pipeline 的固定階段，目前使用內建預設規則；它採 remove-only 設計，不會把它當成任意文字取代工具。

## 段落模式

Parser 預設使用 `wrapped` 模式：連續的非空白行視為同一個邏輯段落，空白行才結束段落。這保留傳統 TXT 的多行段落行為。

對於中文網路小說常見的「一行就是一個段落」TXT，可以明確指定 `line` 模式：

```bash
novel-epub build novel.txt \
  --title "侯夫人与杀猪刀" \
  --author "作者" \
  --paragraph-mode line
```

`line` 模式只改變段落邊界，不依靠標點、句長或其他內容啟發式來推測結構；章節與番外標題仍由既有 grammar 獨立辨識。空白行也不會產生空的 `Paragraph`。

## Full Source Mode

如果希望停用內容 transformation，可以使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --full-source
```

此模式仍會執行 Normalize，因此不是 byte-for-byte 的原始檔複製。其處理路徑是：

```text
TXT → Normalize → Parser → Intermediate → EPUB
```

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

預設語言為 `zh-CN`。

## Intermediate

如果需要保留 Intermediate JSON：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate
```

預設會在目前目錄建立 `<輸入檔名>.intermediate`。也可以指定目錄或路徑：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate \
  --intermediate book.intermediate
```

Intermediate 中會包含 transformation audit metadata，方便確認這次 build 使用了哪些 transformation 及其結果。

## 驗證 EPUB

`build` 完成後會執行內建 EPUB 結構驗證。也可以單獨驗證既有 EPUB：

```bash
novel-epub validate book.epub
```

若系統中存在 EPUBCheck，`validate` 也會執行外部標準驗證；沒有安裝 EPUBCheck 時，內建驗證仍可使用，但會提示外部驗證被略過。

## 常見問題

### 找不到 Pandoc

如果出現找不到 `pandoc` 的錯誤，請先確認：

```bash
pandoc --version
```

如果指令不存在，請先安裝 Pandoc，並確認它位於 `PATH`。

### 中文顯示錯誤

如果 TXT 是 Big5、GBK 或 GB18030 等編碼，請明確指定來源編碼，例如：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding big5
```

### 不想轉換簡體中文

使用 `--no-opencc`。如果同時希望保留原始文字的內容 transformation 行為，也可以直接使用 `--full-source`；Full Source Mode 會停用 OpenCC、Punctuation Conversion 與其他內容 transformation，但仍執行 Normalize。

### 不想轉換標點

使用 `--no-punctuation`。這不會停用 OpenCC。

## 功能

- **V1** — 穩定的 TXT 解析、Intermediate、Pandoc EPUB 產生與驗證。
- **V2** — Normalize、Junk Cleaner、OpenCC、Punctuation Conversion、Full Source Mode、CLI、transformation audit metadata，以及相關 transformation / integration 能力。
- **V2.1 Typography / Layout** — 建立段落邊界語義、hard line break、語義化 HTML/CSS、章節分頁意圖與基礎排版支援。

## 文件

`docs/` 主要保存專案架構、設計決策與跨 session 的工作交接資訊：

- `docs/README.md` — 文件地圖與資訊分層。
- `docs/v1-architecture-decisions.md` — V1 canonical architecture / behavior。
- `docs/v2-migration-and-design-decisions.md` — V2 canonical architecture / decisions。
- `docs/v2.1-typography-and-layout.md` — V2.1 Typography / Layout design baseline。
- `docs/next-session-handoff.md` — 下一個未完成工作的短期交接狀態。

## 授權

MIT
