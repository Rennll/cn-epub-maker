# cn-epub-maker V1 使用說明

`cn-epub-maker` V1 是一個將中文小說 TXT 轉換成 EPUB 的最小化工具。V1 的重點不是完整複刻舊版 `cn-epub-maker`，而是建立一條穩定、可驗證、以 Pandoc 為主要 EPUB backend 的新架構。

V1 以「盡量保持原文」為核心原則：Normalize 會整理輸入檔案的表示方式，Parser 會辨識卷、章、段落結構，EPUB renderer 會負責輸出電子書；不會在核心流程中自行進行簡繁轉換、內容清理或其他語意性的文字改寫。

## 目前功能

V1 提供以下基本能力：

- 讀取中文 TXT 檔案。
- 自動偵測常見中文編碼，包括 UTF-8、GB18030、GBK 與 Big5；也支援手動指定編碼。
- 處理 UTF-8 BOM。
- 統一 CRLF、CR 與 LF newline 表示。
- 移除段首用於排版縮排的全形空格，同時保留其他原文內容。
- 將 TXT 解析為 `Book → Volume → Chapter → Paragraph` 結構。
- 對 Parser 無法完全判斷的情況提供 warning，而不是無條件停止整個流程。
- 產生 Intermediate JSON，方便處理大量章節並進行後續渲染。
- 使用 Pandoc 將內容轉換為 EPUB。
- 支援書名、作者、語言與封面等基本 EPUB metadata。
- 產生目錄與卷／章層級結構。
- 對 EPUB 結構進行基本檢查。
- 可使用 EPUBCheck 進行額外的 EPUB 標準驗證。

## 安裝

本專案使用 Python 3.10 以上版本。

建議先安裝專案本身：

```bash
python3 -m pip install -e .
```

EPUB 產生依賴 Pandoc，請確認系統可以執行 `pandoc`：

```bash
pandoc --version
```

如果要進行 EPUBCheck，另外需要安裝 EPUBCheck executable，並讓它可以從 PATH 找到。

OpenCC、Junk Cleaner 與其他文字 transformation 屬於後續 V2 擴充方向，**不是 V1 的必要安裝項目**。

## 基本使用

最基本的 build 指令是：

```bash
novel-epub build novel.txt --title "書名" --author "作者"
```

也可以使用 Python module 方式執行：

```bash
python3 -m novel_epub.cli build novel.txt --title "書名" --author "作者"
```

成功後會在輸入檔案所在目錄產生 EPUB。若要指定輸出檔案：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --output book.epub
```

指定來源編碼時可以使用 `--encoding`：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --encoding gb18030
```

如果希望同時保留 Intermediate 資料，可以使用：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate
```

也可以指定 Intermediate 輸出位置：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --keep-intermediate \
  --intermediate book.intermediate
```

加入封面：

```bash
novel-epub build novel.txt \
  --title "書名" \
  --author "作者" \
  --cover cover.jpg
```

## 驗證 EPUB

可以直接對既有 EPUB 執行內建結構驗證：

```bash
novel-epub validate book.epub
```

V1 的 validation 分成兩個層次。第一層是程式內建的 EPUB 結構檢查，例如 `container.xml`、OPF、manifest、spine、navigation 等檔案與引用關係；第二層是 EPUBCheck 的外部標準驗證。

如果 EPUBCheck executable 不存在，內建結構檢查仍然可以執行，EPUBCheck 會被跳過並提示 warning。這不會把「系統沒有安裝 EPUBCheck」本身視為 EPUB 結構錯誤。

如果 EPUBCheck 找到真正的 EPUB 錯誤，`validate` 會回傳非零 exit code。

## 輸出流程

V1 的核心流程如下：

```text
TXT
 ↓
Normalize
 ↓
Parser
 ↓
Book
 ↓
Intermediate JSON
 ↓
Markdown
 ↓
Pandoc
 ↓
EPUB
 ↓
EPUB validation
 ↓
EPUBCheck（若已安裝）
```

這種設計刻意把「文字輸入處理」、「文件結構解析」、「Intermediate」與「EPUB rendering」分開。尤其 Parser 不應該同時負責文字轉換或 EPUB package assembly。

## 注意事項

### V1 不會自動把簡體轉成繁體

雖然舊版工具提供 OpenCC 簡轉繁，但這不是 V1 核心 pipeline 的功能。V1 的目標是先建立穩定的 text-preserving foundation；OpenCC 預設開啟、可關閉，以及 conversion profile 等行為已列為 V2 的設計決策。

因此，如果你的主要需求是「簡體 TXT 直接輸出繁體 EPUB」，目前不應把 V1 當成完整的舊版替代品。

### V1 不會自動清除廣告或垃圾內容

V1 不會自行判斷某段文字是不是廣告、網址、分隔線或其他垃圾內容。這是刻意的，因為自動清理容易誤刪正文。

V2 預計加入使用者自行指定規則的 Junk Cleaner，而且會採 remove-only 設計。規則會明確指定 `line` 或 `block` target，以及 `exact`、`contains` 或 `regex` matcher。

### V1 不會重新編號章節

來源檔案中的章節編號會被視為原始內容的一部分。V1 不會因為發現跳號、重複或缺章而自行重新編號。

這是刻意避免破壞正文中可能存在的「第 X 章」交叉引用。舊版的 chapter renumbering 不屬於 V1 migration baseline。

### V1 不會把阿拉伯數字全部轉成中文數字

日期、時間、ISBN、網址、版本號、ID、數學式等內容都可能包含阿拉伯數字。全域轉換容易造成不預期的文字變更，因此 Arabic numeral conversion 不屬於 V1。

### Warning 不一定代表產出失敗

Parser 或 validation 遇到不影響 EPUB 產出的問題時，可以使用 warning 告知使用者並繼續處理。真正阻止輸出的情況才會回傳 error。

因此使用工具時，除了 exit code，也應注意 stderr 中的 `WARNING:` 訊息。

## 原文保留模式的概念

V1 本身就是以 text-preserving 為目標的最小 pipeline。未來 V2 即使加入 OpenCC、Junk Cleaner、Quote Conversion 等 transformation，也會保留一條完整原文模式：

```text
Normalize
 ↓
Parser
```

這裡的「完整原文」指不主動進行內容 transformation，而不是 byte-for-byte 保留原始 TXT。Normalize 仍可能改變 BOM、newline representation、encoding interpretation，以及定義中的段首全形空格等輸入表示方式。

## 大型作品

Intermediate layer 的設計是為了避免把整本小說的所有內容都綁死在單一 EPUB rendering operation 中。Chapter 可以獨立序列化成 JSON，因此數千章的作品仍可以使用相同的 pipeline 處理。

實際大型作品仍應注意磁碟空間與 Pandoc 所需的處理時間；V1 不保證任意大小的小說都能在有限資源下完成。

## V1 與後續 V2

V1 的主要目的已經完成：建立穩定的 Model、Normalize、Parser、Intermediate、Pandoc EPUB renderer 與 Validation 基礎。V2 不會重新設計這些核心部分，而會在其上加入明確隔離的 extension points。

目前已確定的 V2 方向包括：

- OpenCC：預設開啟，可關閉，並保留 conversion profile 擴充能力。
- Junk Cleaner：獨立規則檔、使用者指定規則、`line` / `block` target、`exact` / `contains` / `regex` matcher，並提供每條規則的刪除統計。
- Quote Conversion：獨立 transformation。
- Transform failure policy：可安全跳過的問題使用 warning；會使輸出不可信的問題才阻止產出。
- Transformation metadata：只保留在 Intermediate，不寫入 EPUB metadata。
- Arabic numeral conversion 與 chapter renumbering：目前不 migration。

更完整的設計決策請參閱：

- `docs/v1-architecture-decisions.md`
- `docs/v2-migration-and-design-decisions.md`

## 授權

MIT
