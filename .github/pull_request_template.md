## 📋 PR 描述
建立 GitHub Pages 靜態 Dashboard，用於可視化狙擊手系統的績效數據。

此 PR 解決了以下 Issue:
- Closes #[ISSUE_NUMBER]

## ✅ 變更內容
- [ ] 新增 `docs/index.html` - Dashboard 主頁面
- [ ] 新增 `.github/ISSUE_TEMPLATE/dashboard-feature.md` - Issue 範本
- [ ] 新增 `.github/pull_request_template.md` - PR 範本

## 🎯 功能特點
- 使用 TailwindCSS 進行響應式排版
- 使用 Chart.js 繪製準確率趨勢圖表
- 自動從 GitHub Raw JSON 讀取數據 (`data/performance_metrics.json`, `data/telemetry.json`)
- 顯示指標：
  - 當前準確率
  - 總預測次數
  - 當前 Prompt 版本
  - 準確率趨勢圖表
  - 近期預測紀錄表格

## 🔧 技術實作細節
- JavaScript fetch() API 讀取 JSON 數據
- 支援 CORS（GitHub Raw URLs 預設支援）
- 響應式設計（支援手機與桌面）

## 📸 截圖（如有）
請在部署後前往 GitHub Pages 查看實際效果。

## 🚀 部署步驟
1. 合併此 PR 到 main 分支
2. 前往 Repository Settings > Pages
3. 設定 Branch: main, Folder: /docs
4. 等待約 1 分鐘後，Dashboard 將會在以下網址可用：
   `https://eddievibe4tech-byte.github.io/sniper-system-test/`

## 📁 Code Review 重點檔案
| 檔案路徑 | 說明 | Review 重點 |
|----------|------|-------------|
| `docs/index.html` | Dashboard 主頁面 | HTML 結構、JavaScript 邏輯、Chart.js 設定 |
| `.github/ISSUE_TEMPLATE/dashboard-feature.md` | Issue 範本 | 驗收標準完整性 |
| `.github/pull_request_template.md` | PR 範本 | 描述清晰度 |

## ✅ 自我檢查清單
- [ ] 程式碼符合專案規範
- [ ] 已測試本地端開啟 HTML 檔案
- [ ] 已確認 JSON 數據路徑正確
- [ ] PR 描述清楚說明變更內容

---
**備註**: 此 Dashboard 為靜態網頁，無需後端伺服器，完全免費且零維護成本。
