# 產出進度報告

產出一份完整的 V3 Chat Refactor 進度報告，讓 the owner 可以一眼看到整體完成百分比、每個 Phase 的狀態、以及接下來要做什麼。

## 報告語言

繁體中文。

## 報告風格

- 用**功能/產品面描述**為主，不要只列技術術語
- 每個 Phase 要說明「這個 Phase 在做什麼（白話）」+ 技術細節
- 讓 the owner 能估算整體完成百分比
- 包含「已完成」「進行中」「待做」三個區塊
- 每個已完成的 sub-deliverable 要附 commit hash 和一句話說明改了什麼功能

## 執行步驟

1. 讀取 worker 的 git log 確認最新 commit 狀態
2. 讀取 plan doc 確認總共有多少 Phases 和 sub-deliverables
3. 讀取各 Phase preflight 確認每個 Phase 的 sub 數量
4. 比對已完成 vs 待做，算出百分比
5. 檢查是否有待決策的 Tier 3 escalation
6. 產出報告

## 報告格式

```
# V3 Chat Refactor 進度報告
時間：YYYY-MM-DD HH:MM
分支：feature/chat-telegram-refactor-v2

## 整體進度：X / Y 個 sub-deliverables 完成（約 XX%）

---

## Phase 1：建立訊息資料合約（Host DTO）
**白話：** 讓伺服器和 app 之間有一個統一的「訊息格式」，不再各說各話。
**狀態：** 完成 ✅
**Sub-deliverables：**
- ✅ sub #1: ... (commit hash) — 一句話功能描述
- ✅ sub #2: ...
- ✅ sub #3: ...

## Phase 2：媒體附件正規化（Media Refactor）
**白話：** 把圖片和檔案從「文字裡塞路徑」的 hack 方式，改成真正的媒體訊息。
**狀態：** 完成 ✅ / 進行中 🔧 / 待做 ⏳
**Sub-deliverables：**
- ✅ sub #1: ... — ...
- 🔧 sub #2: ... — 正在做...
- ⏳ sub #3: ... — 還沒開始

## Phase 3：對話分支/複製/重開（Branch-Copy-Reopen）
**白話：** 讓「繼續上次對話」和「從某個點分支出新對話」的功能更穩定可靠。
...

## Phase 4：Postbox 整合
**白話：** 讓 app 內部的訊息儲存從自製方案切換到 Telegram 原生的儲存機制。
...

## Phase 5：UI 接管
**白話：** 讓聊天畫面從自製的 SwiftUI 殼切換到 Telegram 原生的聊天框架。
...

---

## 待決策事項
（如果有 Tier 3 escalation 待決）

## 備註
- Phase 4 前置條件：downloader ownership 遷移尚未承諾
- 其他值得注意的事項
```

## 資料來源

- Git log: `git -C <worker_working_dir> log --oneline feature/chat-telegram-refactor-v2`
- Plan doc: `prompts/20260416_1_host_message_based_refactor_plan.md`
- Phase preflights: `prompts/20260417_*_phase*_preflight.md`
- Escalation reports: `prompts/20260417_*_escalation_*.md`
- _REMINDER.md: 本 repo 的 `prompts/_REMINDER.md`

## 執行方式

1. 先問 worker 跑 `git log --oneline` 取得最新 commit 列表
2. 讀取各 preflight 文件確認 sub 數量
3. 比對 commit messages 與 preflight sub 列表
4. 檢查 _REMINDER.md 中的待決策事項
5. 產出報告給 the owner

## 注意事項

- 這是 manager-side 的報告產出，不需要改任何程式碼
- 報告直接輸出在對話中（Telegram-friendly），不寫成檔案
- 如果 worker 正在工作中，標注「進行中」並說明目前在做什麼
- 百分比計算：已完成 sub 數 / 總 sub 數（across all phases）
