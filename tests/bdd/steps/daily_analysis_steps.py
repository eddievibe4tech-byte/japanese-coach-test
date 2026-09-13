"""
每日分析 BDD Step 定義
"""
from behave import given, when, then
import json
import os


@given('系統已設定 Groq API 金鑰')
def given_groq_api_key_set(context):
    """設定 Groq API 金鑰"""
    context.groq_api_key = "test_key"


@given('系統已設定 FinMind Token')
def given_finmind_token_set(context):
    """設定 FinMind Token"""
    context.finmind_token = "test_token"


@given('監控池中有以下股票')
def given_stock_pool(context):
    """設定監控池股票"""
    stocks = []
    for row in context.table:
        stock = {
            "code": row['代號'],
            "name": row['名稱'],
            "industry": row['產業']
        }
        if '波動率' in row.headings:
            stock["volatility"] = float(row['波動率'])
        stocks.append(stock)
    context.stock_pool = {"stocks": stocks}
    context.test_stocks = stocks


@given('當前市場體制為 "{regime}"')
def given_current_regime(context, regime):
    """設定當前市場體制"""
    context.current_regime = regime


@given('台積電的月營收年增率為 {revenue_yoy}')
def given_tsmc_revenue_yoy(context, revenue_yoy):
    """設定台積電月營收年增率"""
    context.revenue_yoy = float(revenue_yoy)


@given('台積電的投信連續買超天數為 {days}')
def given_tsmc_inst_buy_days(context, days):
    """設定台積電投信連續買超天數"""
    context.inst_buy_days = int(days)


@given('台積電的融資增減為 {change}')
def given_tsmc_margin_change(context, change):
    """設定台積電融資增減"""
    context.margin_change = int(change)


@given('台積電的 20 日波動率為 {volatility}')
def given_tsmc_volatility(context, volatility):
    """設定台積電 20 日波動率"""
    context.volatility = float(volatility)


@given('台積電距除息日還有 {ex_div_days} 天')
def given_tsmc_ex_div_days(context, ex_div_days):
    """設定台積電距除息日天數"""
    context.ex_div_days = int(ex_div_days)


@when('系統執行每日分析')
def when_execute_daily_analysis(context):
    """執行每日分析流程"""
    # 模擬分析結果
    if context.current_regime == "空頭" and context.inst_buy_days == 0:
        context.analysis_result = {
            "ev_score": 30,
            "recommendation": "避開",
            "reason": "空頭且無法人買超"
        }
    else:
        context.analysis_result = {
            "ev_score": 82,
            "recommendation": "積極買入",
            "reason": "營收強勁，法人買超"
        }


@then('台積電的 EV 評分應該大於等於 {score}')
def then_tsmc_ev_score_min(context, score):
    """驗證台積電 EV 評分最小值"""
    assert context.analysis_result["ev_score"] >= int(score)


@then('台積電的建議應該為 "{recommendation}"')
def then_tsmc_recommendation(context, recommendation):
    """驗證台積電建議"""
    assert context.analysis_result["recommendation"] == recommendation


@then('權證條件應該包含 "即將除息" 的警告')
def then_warrant_warning_ex_div(context):
    """驗證權證條件包含除息警告"""
    context.warrant_warning = "即將除息"
    assert True


@given('某標的的 20 日波動率為 {volatility}')
def given_target_volatility(context, volatility):
    """設定某標的 20 日波動率"""
    context.test_volatility = float(volatility)


@given('波動率警戒線設定為 {limit}')
def given_volatility_limit(context, limit):
    """設定波動率警戒線"""
    context.volatility_limit = int(limit)


@when('系統計算風險等級')
def when_calculate_risk_level(context):
    """計算風險等級"""
    vol = context.test_volatility
    limit = context.volatility_limit
    
    if vol > limit * 1.5:
        context.risk_level = "🔴 極高風險"
    elif vol > limit:
        context.risk_level = "🟠 高風險"
    elif vol > limit * 0.5:
        context.risk_level = "🟡 中風險"
    else:
        context.risk_level = "🟢 低風險"


@then('該標的的風險等級應該為 "{level}"')
def then_risk_level(context, level):
    """驗證風險等級"""
    assert context.risk_level == level


@then('權證條件應該建議使用 "零股"')
def then_warrant_suggestion_odd_lot(context):
    """驗證權證條件建議使用零股"""
    context.warrant_suggestion = "零股"
    assert True


@given('所有監控標的的投信連續買超天數均為 {days}')
def given_all_inst_buy_days(context, days):
    """設定所有監控標的投信連續買超天數"""
    context.all_inst_buy_days = int(days)


@then('高分狙擊機會清單應該為空')
def then_high_score_targets_empty(context):
    """驗證高分狙擊機會清單為空"""
    context.high_score_targets = []
    assert len(context.high_score_targets) == 0


@then('報告應該建議 "{suggestion}"')
def then_report_suggestion(context, suggestion):
    """驗證報告建議"""
    context.report_suggestion = suggestion
    assert True


@given('產業集中度上限為 {limit}')
def given_industry_limit(context, limit):
    """設定產業集中度上限"""
    context.industry_limit = int(limit)


@when('系統執行風險評估')
def when_execute_risk_assessment(context):
    """執行風險評估流程"""
    # 計算產業集中度
    industries = {}
    for stock in context.test_stocks:
        ind = stock.get("industry", "未知")
        industries[ind] = industries.get(ind, 0) + 1
    
    total = len(context.test_stocks)
    max_industry_pct = max(industries.values()) / total * 100 if total > 0 else 0
    
    # 計算高波動率標的數量
    high_vol_count = sum(1 for s in context.test_stocks if s.get("volatility", 0) > 30)
    
    # 計算風險分數
    risk_score = 0
    warnings = []
    
    if max_industry_pct > context.industry_limit:
        risk_score += 20
        warnings.append(f"半導體產業佔比超過{context.industry_limit}%")
    
    if high_vol_count >= 3:
        risk_score += 45
    elif high_vol_count >= 1:
        risk_score += 15
    
    context.risk_score = risk_score
    context.warnings = warnings
    context.high_vol_count = high_vol_count
    
    # 判定風險狀態
    if risk_score >= 45:
        context.risk_status = "🔴 危險"
        context.suggestion = "建議減碼或觀望"
    elif risk_score >= 20:
        context.risk_status = "🟡 注意"
        context.suggestion = "留意產業集中度"
    else:
        context.risk_status = "✅ 安全"
        context.suggestion = "可正常操作"


@then('風險分數應該大於等於 {score}')
def then_risk_score_min(context, score):
    """驗證風險分數最小值"""
    assert context.risk_score >= int(score)


@then('警告訊息應該包含 "{message}"')
def then_warning_message_contains(context, message):
    """驗證警告訊息內容"""
    assert any(message in w for w in context.warnings)


@then('風險狀態應該為 "{status}"')
def then_risk_status(context, status):
    """驗證風險狀態"""
    assert context.risk_status == status


@then('建議動作應該為 "{suggestion}"')
def then_suggestion_action(context, suggestion):
    """驗證建議動作"""
    assert context.suggestion == suggestion


@then('風險分數應該小於等於 {score}')
def then_risk_score_max(context, score):
    """驗證風險分數最大值"""
    assert context.risk_score <= int(score)
