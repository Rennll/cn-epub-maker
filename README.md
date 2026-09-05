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

OpenCC 預設啟用，可以用 `--no-opencc` 停用：

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

### Junk Cleaner

Junk Cleaner 是文字處理 pipeline 中的固定階段，負責依照明確規則移除來源文字中的非正文內容。目前 CLI 建立的 Junk Cleaner 沒有套用預設規則，因此**不會主動刪除任何小說內容**。

Junk Cleaner 的規則目前是程式內部的 `JunkRule`，每條規則包含三個欄位：

- `target`：匹配範圍，目前支援 `line` 與 `block`。
- `matcher`：匹配方式，目前支援 `exact`、`contains` 與 `regex`。
- `pattern`：要匹配的文字或正則表達式。

例如，規則可以表示為：

```python
JunkRule(
    target="line",
    matcher="exact",
    pattern="本章節完",
)
```

`target="line"` 表示逐行判斷。上面的規則只有在某一整行完全等於 `本章節完` 時才會移除該行。

`target="block"` 則以空白行分隔的連續非空白行作為一個區塊判斷。例如：

```python
JunkRule(
    target="block",
    matcher="contains",
    pattern="本章由",
)
```

如果某個連續文字區塊中包含 `本章由`，整個區塊會被移除。因此 `block` 規則要比 `line` 規則更加謹慎。

三種 matcher 的行為如下：

- `exact`：目標內容必須與 `pattern` 完全相等。
- `contains`：目標內容只要包含 `pattern` 即視為命中。
- `regex`：使用 Python 正則表達式進行匹配。

例如，固定文字適合使用 `exact`：

```python
JunkRule(
    target="line",
    matcher="exact",
    pattern="請收藏本書",
)
```

文字可能出現在不同位置時，可以使用 `contains`：

```python
JunkRule(
    target="line",
    matcher="contains",
    pattern="本小說由",
)
```

需要處理固定結構、但部分文字會變動時，可以使用 `regex`：

```python
JunkRule(
    target="line",
    matcher="regex",
    pattern=r"^本章由.*整理$",
)
```

多條規則可以組合使用：

```python
rules = [
    JunkRule(
        target="line",
        matcher="exact",
        pattern="本章節完",
    ),
    JunkRule(
        target="line",
        matcher="contains",
        pattern="請收藏本書",
    ),
    JunkRule(
        target="line",
        matcher="regex",
        pattern=r"^本章由.*整理$",
    ),
]
```

目前這些規則並不是使用者可直接透過 CLI 指定的設定檔；它們是 `JunkCleaner` 的程式內部介面。這部分的使用者自訂規則與規則載入方式尚未定義，因此 README 目前不提供虛構的 `--junk-rules` 或 JSON/YAML 設定檔用法。

撰寫規則時，應盡量使用最具體的匹配條件，只移除可以明確判定為非正文的內容。尤其是 `contains` 與 `regex`，如果條件過於寬鬆，可能誤刪正常小說內容。Junk Cleaner 的用途是 remove-only，不應拿來進行一般文字替換或正文改寫。

## 段落模式

`build` 提供 `--paragraph-mode`，用來指定 TXT 的段落邊界語義。預設為 `wrapped`，因此不指定此參數時，行為與既有傳統 TXT 解析相同：連續的非空白行視為同一個邏輯段落，空白行才結束段落。

如果來源是中文網路小說常見的「一行就是一個段落」格式，可以指定 `line`：

```bash
novel-epub build novel.txt \
  --title "侯夫人与杀猪刀" \
  --author "作者" \
  --paragraph-mode line
```

兩種模式的差異是：

- `wrapped`：連續非空白行合併為一個段落；來源行中的換行可保留為該段落內的 hard line break。
- `line`：每個非空白來源行各自成為一個段落。
- 兩種模式都不會因空白行產生空的 `Paragraph`。
- `--paragraph-mode` 是明確的輸入格式選擇，不會根據標點、句長、縮排等內容啟發式自動判斷。
- 章節、卷與番外標題的辨識與段落模式獨立，不會因切換模式而改變既有 heading grammar。

因此，只有在來源 TXT 確實採用「一行一段」格式時才需要使用 `--paragraph-mode line`；一般傳統 TXT 建議維持預設的 `wrapped`。

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

Intermediate 是 build 過程中的結構化書籍資料。只有使用 `--keep-intermediate` 時，程式才會把它寫到磁碟，方便檢查 Parser 結果與 transformation audit。

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate
```

如果沒有指定 `--intermediate`，例如輸入檔為 `novel.txt`，預設會在目前目錄建立 `novel.intermediate/`。也可以指定 Intermediate 根目錄：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate \
  --intermediate book.intermediate
```

Intermediate 實際輸出結構如下：

```text
novel.intermediate/
├── book.json
├── preamble.json          # 有前言時才會產生
└── chapters/
    ├── 000001.json
    ├── 000002.json
    └── ...
```

`book.json` 保存書籍 metadata、卷章索引，以及這次 build 的 transformation audit。各章內容則寫在 `chapters/` 下的 JSON 檔案中；如果書籍有 preamble，則另外保存為 `preamble.json`。

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

## 授權

MIT
