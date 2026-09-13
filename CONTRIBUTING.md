# 🏗️ 狙擊手系統開發與維護 Checklist

這份 Checklist 彙整了過去 Code Review 中發現的關鍵問題與最佳實踐。未來在開發新功能或修改程式碼時，請隨時對照此清單，可避開 90% 以上的常見陷阱！

---

## 📑 目錄

1. [系統架構與 Python 工程實踐](#-一系統架構與-python-工程實踐)
2. [外部 API 串接 (FinMind & Groq)](#-二外部-api-串接-finmind--groq)
3. [金融數學與風險邏輯](#-三金融數學與風險邏輯)
4. [前端儀表板 (HTML/JS & UI/UX)](#-四前端儀表板-htmljs--uiux)
5. [CI/CD (GitHub Actions) 與自動化](#-五-cicd-github-actions-與自動化)
6. [測試與 BDD 規範](#-六測試與-bdd-規範)

---

## 🏗️ 一、系統架構與 Python 工程實踐

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **路徑處理** | ❌ 避免使用 `'data/file.json'` 等硬編碼相對路徑。<br>✅ 務必使用 `Path(__file__).resolve().parent.parent` 動態取得專案根目錄，確保在任何環境下執行都不會報錯。 |
| **時區處理** | ❌ 避免使用 `datetime.now()` (會抓到伺服器 UTC 時間)。<br>✅ 務必使用 `datetime.now(TZ_TAIPEI)`，確保產出的 JSON 與 Log 檔案名稱符合台灣盤後時間。 |
| **檔案 I/O 效能** | ❌ 避免在 `for` 迴圈內頻繁「讀取 -> 修改 -> 寫入」同一個 JSON 檔 (如 `telemetry.json`)。<br>✅ 務必在迴圈外讀取，在記憶體中批次 Append，最後**一次性寫入**，避免 I/O 瓶頸與檔案鎖死 (Race Condition)。 |
| **日誌設定** | ❌ 避免直接呼叫 `logging.basicConfig()` 而不加檢查。<br>✅ 務必加入 `if logger.hasHandlers(): logger.handlers.clear()`，避免測試或重試時 Log 重複印出。 |
| **狀態判定** | ❌ 避免只要主程式沒崩潰就回傳 `success`。<br>✅ 若批次任務中部分項目失敗 (如 10 檔股票失敗 2 檔)，應將狀態標記為 `partial` 並記錄 Warning。 |

---

## 🤖 二、外部 API 串接 (FinMind & Groq)

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **FinMind API** | ❌ URL 路徑錯 (`/api/v3/data/dataset`)、JSON 多包一層 (`data.data`)。<br>✅ 正確 Endpoint 為 `/api/v4/data`，參數需透過 Query 傳遞；回傳的 `data` 鍵直接對應 **List (陣列)**。 |
| **Groq API** | ❌ 忘記帶 Header 或重試次數語意不清。<br>✅ 確保請求帶有 `Authorization: Bearer <KEY>`；明確區分 `max_retries` (重試次數) 與 `max_attempts` (總嘗試次數)。 |
| **版本控制** | ❌ Prompt 版本或模型名稱寫死 (如 `'prompt_version': 1`)。<br>✅ 務必從 `prompt_history.json` 或 `.env` 動態讀取，確保未來自動優化 Prompt 後，新預測能掛載正確的版本號。 |
| **API 錯誤處理** | ❌ 網路超時直接讓主程式崩潰。<br>✅ 實作指數退避 (Exponential Backoff) 重試機制，並將 API 失敗視為「該筆預測無效」，不應中斷整體分析流程。 |

---

## 💰 三、金融數學與風險邏輯

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **波動率計算** | ❌ 使用簡單報酬率與母體變異數 (除以 N)。<br>✅ 量化標準做法：使用**對數報酬率 (Log Returns)** 與**樣本變異數 (除以 N-1)**，並乘以 $\sqrt{252}$ 年化。 |
| **產業集中度** | ❌ 僅計算「股票檔數」佔比 (會嚴重失真)。<br>✅ 必須基於**資金權重 (Weight / Value)** 來計算產業集中度，才能真實反映風險暴露。 |
| **除以零防護** | ❌ 計算漲跌幅 `prices[-1] / prices[-6]` 時未檢查分母。<br>✅ 務必加入 `prices[-6] != 0` 的防護，避免極端異常資料導致 `ZeroDivisionError` 中斷迴圈。 |

---

## 🎨 四、前端儀表板 (HTML/JS & UI/UX)

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **型別與 XSS 防護** | ❌ `escapeHTML` 使用 `if (!str)`，會把數字 `0` 誤判為空值而顯示 `-`。<br>✅ 務必精確判斷 `if (str === null \|\| str === undefined)`。所有動態插入 HTML 的數據都必須經過跳脫 (Escape)。 |
| **錯誤隔離** | ❌ 多個 `fetch` 請求中，只要一個 JSON 解析失敗，整個頁面停止渲染。<br>✅ 務必將每個 `.json()` 解析獨立包裹在 `try-catch` 中，確保「股票池壞掉，不影響今日分析表格」。 |
| **圖表渲染** | ❌ 刷新頁面或重新載入數據時，直接在舊 Canvas 上 `new Chart()`。<br>✅ 務必將 Chart 實例存為變數，在重新繪製前呼叫 `chartInstance.destroy()`，避免 Canvas 衝突報錯。 |
| **資料排序** | ❌ 遍歷 Object 繪製趨勢圖，導致 X 軸版本號錯亂 (如 V10 排在 V2 前面)。<br>✅ 務必在餵給 Chart.js 前，對 Labels 進行**顯式排序 (Explicit Sort)**。 |

---

## 🚀 五、CI/CD (GitHub Actions) 與自動化

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **寫入權限** | ❌ Workflow 執行 Auto-commit 時遇到 403 Forbidden。<br>✅ YAML 頂層務必加上 `permissions: contents: write`。 |
| **Commit 路徑** | ❌ `file_pattern` 包含不存在的目錄 (如 `logs/*.log`) 導致 `git add` 報錯退出。<br>✅ 建議改用 `file_pattern: '.'`，並搭配嚴格的 `.gitignore` 來排除 Log 與快取。 |
| **排程分離** | ❌ 每日 Cron 排程中執行完整的 `pytest` 與 `behave` 測試。<br>✅ 排程應專注於「執行生產任務」；完整的單元/BDD 測試應放在 `on: [push, pull_request]` 觸發。 |
| **Secrets 管理** | ❌ 將 Token 寫死在程式碼或 `.env` 中並 Commit。<br>✅ 務必使用 GitHub Repository Secrets 注入，程式碼透過 `os.environ.get()` 讀取。 |

---

## 🧪 六、測試與 BDD 規範

| 檢查項目 | 常見陷阱 / 規範建議 |
| :--- | :--- |
| **Step 命名** | ❌ 所有 Step 函數都命名為 `step_impl`，導致 IDE 無法跳轉且除錯困難。<br>✅ 務必使用具備描述性的函數名稱 (如 `given_prediction_records_count`)。 |
| **邏輯抽離** | ❌ 在 BDD 的 `@when` 或 `@then` 中撰寫 `if/else` 業務邏輯。<br>✅ Step 定義應只負責「準備資料、呼叫 SUT (System Under Test)、驗證結果」，核心邏輯必須封裝在 `src/` 的類別中。 |
| **OpenAPI 語法** | ❌ Enum 陣列使用全形逗號 `[多頭，震盪，空頭]`。<br>✅ YAML 中的陣列必須使用半形逗號加空格 `["多頭", "震盪", "空頭"]` 或標準 `-` 列表，否則會被解析為單一長字串。 |

---

## 💡 總結建議

您目前的「狙擊手系統」已經具備了非常優秀的骨架。未來若要進一步擴展（例如：加入更多股票、串接真實券商 API 下單、或是實作 T+N 的準確率回填機制），只要嚴格遵守上述的 **「批次 I/O」**、**「錯誤隔離」** 與 **「金融數學規範」**，您的系統就能穩健地擴展，不會因為資料量變大而崩潰！
