# cn-epub-maker

將中文小說 TXT 轉換成 EPUB 的 Python 工具。

目前 `main` 上的穩定基線是 V1：重點是以保留原文為優先，解析卷／章／段落結構，產生 Intermediate，再透過 Pandoc 建立 EPUB 並進行結構驗證。

V1 不會自動進行簡體轉繁體、垃圾內容清理、全域阿拉伯數字轉換或章節重新編號。這些屬於 V2 的後續設計；V2 目前尚未完整實作。

## 安裝

需要 Python 3.10 以上，以及可執行的 Pandoc。

```bash
python3 -m pip install -e .
pandoc --version
```

EPUBCheck 為選用工具。安裝後放在 `PATH` 中即可讓 `validate` 額外執行 EPUB 標準驗證。

## 快速使用

基本 build：

```bash
novel-epub build novel.txt --title "書名" --author "作者"
```

也可以使用 Python module 方式執行：

```bash
python3 -m novel_epub.cli build novel.txt --title "書名" --author "作者"
```

指定輸出檔案：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --output book.epub
```

指定來源編碼：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding gb18030
```

加入封面：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --cover cover.jpg
```

如果需要保留 Intermediate：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate
```

也可以指定 Intermediate 目錄：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate \
  --intermediate book.intermediate
```

驗證既有 EPUB：

```bash
novel-epub validate book.epub
```

## 目前 V1 提供的能力

- 讀取 TXT，支援常見中文編碼並可手動指定編碼。
- 處理 UTF-8 BOM 與不同 newline 表示。
- 移除定義中的段首全形空格縮排。
- 解析 `Book → Volume → Chapter → Paragraph` 結構。
- 支援阿拉伯數字與定義範圍內的中文章節數字。
- 保留卷、章、段落與章節原始 label 等結構資訊。
- 保留第一個章節之前的前言內容。
- 支援明確格式的番外章節。
- 對可繼續處理的輸入異常提供 warning，而不是任意猜測。
- 產生 Intermediate JSON，適合大量章節的作品。
- 使用 Pandoc 建立 EPUB。
- 支援書名、作者、語言與封面等基本 metadata。
- 提供內建 EPUB 結構驗證，並可選擇使用 EPUBCheck。

## V1 的設計原則

V1 將「文字表示」、「文件結構」、「Intermediate」與「EPUB rendering」分開：

```text
TXT
 ↓
Normalize
 ↓
Parser
 ↓
Intermediate
 ↓
Pandoc
 ↓
EPUB
 ↓
Validation
```

Parser 以明確 grammar 判斷卷章結構，不進行語意猜測。章節的 `number`、`label`、`sequence` 也刻意分開，因此跳號、重複編號與番外章節不需要被重新編號。

更多 V1 行為與邊界請參閱 `docs/v1-architecture-decisions.md`。

## V1 與 V2

V1 是目前穩定基線。V2 會在 V1 上加入明確隔離的文字 transformation 與 presentation extension，而不是重新建立舊版架構。

目前已確定的 V2 設計包括：

- OpenCC：預設啟用，可停用，並保留 conversion profile 擴充能力。
- Junk Cleaner：使用者指定規則、`line` / `block` target、`exact` / `contains` / `regex` matcher，並採 remove-only 設計。
- Quote Conversion：獨立 transformation，要求明確且可重複套用而不產生額外變化。
- Full Source Mode：停用內容 transformation，但仍執行 Normalize。
- Transformation metadata：記錄在 Intermediate，不寫入 EPUB metadata。
- Arabic numeral conversion 與 chapter renumbering：不列入 V2 migration baseline。

V2 的完整設計與 migration decisions 請參閱 `docs/v2-migration-and-design-decisions.md`。

## 文件

`docs/` 主要供 AI 與跨 session 工作使用：

- `docs/README.md` — 文件地圖與資訊分層。
- `docs/v1-architecture-decisions.md` — V1 canonical architecture / behavior。
- `docs/v2-migration-and-design-decisions.md` — V2 canonical design / decisions。
- `docs/next-session-handoff.md` — 當前未完成工作的短期交接狀態。

## 授權

MIT
