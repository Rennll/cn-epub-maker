# Handoff：Chinese Chapter Numbers / Chapter Header Parser

## Priority

下一個 session 的第一優先事項是完成 `feature/chinese-chapter-numbers`。

**不要在下一個 session 開始處理 V2 額外功能。** V2 規格可以保留作為背景，但目前暫停，直到本 feature 完成、測試通過並完成 integration sanity check。

## Current branch

`feature/chinese-chapter-numbers`

Base：`main`

目前 branch 已有少量 implementation 變更，但尚未視為完成。下一個 session 必須先檢查目前 diff，再依 TDD 順序整理與繼續。

## 已定案規格

### Chapter header

Header 是來源 TXT 中表示新 Chapter 開始的結構行；不是 Markdown heading，也不代表要修改原始文字。

Parser 應優先辨識明確格式，不做「看起來像標題」的猜測。

正式 Chapter header 支援：

- 阿拉伯數字，例如 `第100章`、`第 100 章`
- 中文數字，例如 `第一章`、`第一百章`、`第一百零一章`
- 中文數字支援十、百、千、萬等位階與零位補位
- Chapter 可以沒有 title

中文數字 conversion 必須是 deterministic parsing。無法可靠解析的格式不得被強制轉換。

### number / label / sequence

這三個概念必須分開：

- `number`：來源章節編號的 normalized numeric value；沒有數字時可以是 `None`（目前 Model 若型別仍是 string，需要評估最小變更）
- `label`：保留來源中的章節標籤／文字
- `sequence`：Parser 發現閱讀單位的實際順序

`sequence` 不等於 chapter number，也不應因為 renumbering 而修改來源文字。

例如：

```text
第100章
番外1
第101章
```

應該形成類似：

```text
sequence=100, number=100, label="第100章"
sequence=101, number=None, label="番外1"
sequence=102, number=101, label="第101章"
```

### 番外

番外不是特殊資料類型。

只要它符合通用 Chapter header grammar，就和普通 Chapter 一樣進入同一個 sequence。

Parser 不應單純因為看到「番外」這個詞就強制建立 Chapter。

如果某行看起來像番外，但不符合明確 header grammar，不應擅自切成 Chapter；若因此造成內容沒有正常歸屬，才產生 warning。

### Volume / TOC

番外和一般 Chapter 一樣放在 Volume 的 chapter sequence 中。

例如：

```text
第三卷
├── 第100章
├── 番外1
└── 第101章
```

TOC 應同樣呈現：

```text
第三卷
  第100章
  番外1
  第101章
```

TOC 顯示閱讀結構，不顯示內部 sequence 數字。

### Front matter

第一個正式 Chapter 之前的簡介、作品資訊等合法內容應保留，並視為 front matter，不應再產生目前的 `text_before_first_chapter` warning。

如果 front matter 區域中出現符合 Chapter header grammar 的內容，仍應建立 Chapter；不要因為它位於第一個正式 Chapter 前就全部歸類為 front matter。

## 開發順序

下一個 session 嚴格按照：

1. 檢查 branch 現況與目前 implementation diff。
2. 先補 regression tests（TDD），不要先擴充 implementation。
3. 測試至少涵蓋：
   - 阿拉伯數字 header
   - 中文數字 header
   - 複雜中文數字，例如 `第一百零一`
   - 十／百／千／萬及零位補位
   - 無 title 的 Chapter
   - 一般 Chapter → 番外 → 一般 Chapter 的 sequence
   - Volume 中番外的 sequence 與 TOC 順序
   - front matter 不產生 warning
   - 不符合 grammar 的普通文字不被誤切成 Chapter
4. 再修改 Parser / conversion / Model（只有測試證明需要才改 Model）。
5. 跑 targeted tests，再跑完整 test suite。
6. 用實際小說資料驗證，特別是《修真聊天群》的簡介、番外與中文章節編號。
7. Parser feature 完成後，再處理 EPUB ZIP compression。
8. 最後做完整 integration sanity check。

## ZIP compression（尚未處理）

目前已確認 EPUB 檔案可能偏大，疑似 package assembly 沒有對非 `mimetype` 檔案使用 DEFLATE。

預計：

- `mimetype` 維持 `ZIP_STORED`
- 其他文字資源使用 `ZIP_DEFLATED`
- 補 test 確認 compression type
- 完成後重新跑 EPUBCheck

這是獨立且低風險的後續工作，不要讓它搶在 Chapter parser 規格完成之前。

## 已知環境 / Windows issue

使用者環境：Windows 10、PowerShell 7、Python 3.11、uv。

Pandoc 在 Windows console 輸出 Unicode stderr 時曾出現：

```text
hPutChar: invalid argument
```

目前已修正為由 Python capture Pandoc stdout/stderr，避免直接寫 Windows console；實際 build 已成功。這部分不要重新調查，除非新的 regression 出現。

## V2 暫停事項

下一個 session **不要開始 V2**，包括但不限於：

- cleaner 擴充
- quote conversion 的進一步功能
- OpenCC 整合的擴充
- 更進階的非正常文字處理
- 其他已討論但尚未進入目前 feature 的 V2 功能

這些規格已經討論過，但現在 priority 是把 `chinese-chapter-numbers` 做完整。

## 驗收條件

完成前至少確認：

- targeted parser tests 全部通過
- 完整 tests 全部通過
- 中文數字 conversion 有獨立 regression coverage
- 番外 sequence / TOC 順序正確
- front matter 不再被當成未處理內容 warning
- 實際小說 build 成功
- EPUBCheck 通過
- feature branch diff 清楚且只包含本次功能範圍
