---
name: "Dashboard Feature"
about: "建立 GitHub Pages Dashboard 功能"
title: "[Feature] 建立 GitHub Pages 靜態 Dashboard"
labels: ["enhancement", "dashboard"]
assignees: ""
---

## 📋 需求描述
建立一個基於 GitHub Pages 的靜態 Dashboard，用於可視化狙擊手系統的績效數據。

## ✅ 驗收標準
- [ ] 在 `docs/` 資料夾中建立 `index.html`
- [ ] Dashboard 能自動從 GitHub Raw JSON 讀取數據
- [ ] 顯示以下指標：
  - 當前準確率
  - 總預測次數
  - 當前 Prompt 版本
  - 準確率趨勢圖表
  - 近期預測紀錄表格
- [ ] 使用 TailwindCSS 進行排版
- [ ] 使用 Chart.js 繪製圖表
- [ ] 啟用 GitHub Pages (main branch /docs folder)

## 🔗 相關資源
- GitHub Pages 設定：Settings > Pages > Branch: main > Folder: /docs
- 數據來源：
  - `data/performance_metrics.json`
  - `data/telemetry.json`

## 📝 技術實作細節
- 使用 JavaScript fetch() API 讀取 JSON 數據
- 支援 CORS（GitHub Raw URLs 預設支援）
- 響應式設計（支援手機與桌面）
