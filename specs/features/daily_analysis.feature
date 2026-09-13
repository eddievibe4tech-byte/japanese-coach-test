# language: zh-TW

Feature:每日盤後分析
  As an investor
  I want the system to analyze stocks in the pool daily
  So I can get objective investment reference

  Background:
    Given 系統已設定 Groq API 金鑰
    Given 系統已設定 FinMind Token
    Given 監控池中有以下股票
      | 代號 | 名稱   | 產業   |
      | 2330 | 台積電 | 半導體 |
      | 2308 | 台達電 | 電子   |
      | 2881 | 富邦金 | 金融   |

  Scenario:市場體制為震盪時的分析
    Given When前市場體制為 "震盪"
    Given 台積電的月營收年增率為 53.3
    Given 台積電的投信連續買超天數為 5
    Given 台積電的融資增減為 -500
    Given 台積電的 20 日波動率為 18.5
    Given 台積電距除息日還有 5 天
    When 系統執行每日分析
    Then 台積電的 EV 評分應該大於等於 75
    And 台積電的建議應該為 "積極買入"
    And 權證條件應該包含 "即將除息" 的警告

  Scenario:市場體制為空頭時的分析
    Given When前市場體制為 "空頭"
    Given 台積電的月營收年增率為 53.3
    Given 台積電的投信連續買超天數為 0
    Given 台積電的融資增減為 2000
    When 系統執行每日分析
    Then 台積電的建議應該為 "避開"

  Scenario:高波動率標的的風險提示
    Given When前市場體制為 "震盪"
    Given 某標的的 20 日波動率為 45.0
    Given 波動率警戒線設定為 30
    When 系統計算風險等級
    Then 該標的的風險等級應該為 "🟠 高風險"
    And 權證條件應該建議使用 "零股"

  Scenario:無符合條件的標的
    Given When前市場體制為 "空頭"
    Given 所有監控標的的投信連續買超天數均為 0
    When 系統執行每日分析
    Then 高分狙擊機會清單應該為空
    And 報告應該建議 "持有現金"
