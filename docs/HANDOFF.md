# Handoff：下一個 Session 工作順序

## 目前最高優先事項

先完成 `feature/chinese-chapter-numbers`。這是目前唯一應進行的開發工作。

下一個 session **不要開始 V2**。V2 的需求與討論先保留，等本 feature 完整、測試通過並整合後再恢復。

## 執行原則

本次 feature 已完成規格討論，下一個 session 直接進 implementation，但要恢復我們約定的 TDD 順序：

1. 先檢查目前 feature branch 的 diff，因為 branch 上已經有少量 implementation 變更。
2. 補 tests。
3. 確認 tests 能捕捉尚未完成的行為。
4. 再修改 implementation。
5. targeted tests → full test suite → 實際 EPUB build → EPUBCheck。
6. 完成 parser feature 後，再處理 ZIP compression。
7. 最後做 main integration sanity check。

詳細的 Chapter header / Chinese numeral / front matter 規格請看 `docs/HANDOFF_CHINESE_CHAPTER_NUMBERS.md`。

## V2 狀態

V2 暫停，不要在下一個 session 開始處理。

已討論的 V2 方向包括 cleaner、OpenCC、quote conversion、非正常文字處理及其他擴充；這些都不是本次 session 的工作範圍。

## 已完成的背景

V1 基礎架構已經完成並 merge 到 `main`；Pandoc 在 Windows Unicode stderr 的問題也已經修正，實際 Windows 10 / PowerShell 7 / Python 3.11 / uv build 已成功。

目前新的工作集中在更完整的 Chapter header parsing，尤其是中文數字與番外順序。
