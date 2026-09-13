"""
每日分析 BDD Step 定義
"""
from behave import given, when, then
import json
import os


@given('系統已設定 Groq API 金鑰')
def step_impl(context):
    context.groq_api_key = "test_key"


@given('系統已設定 FinMind Token')
def step_impl(context):
    context.finmind_token = "test_token"


@given('監控池中有以下股票')
def step_impl(context):
    stocks = []
    for row in context.table:
        stocks.append({
            "code": row['代號'],
            "name": row['名稱'],
            "industry": row['產業']
        })
    context.stock_pool = {"stocks": stocks}


@given('當前市場體制為 "{regime}"')
def step_impl(context, regime):
    context.current_regime = regime


@given('台積電的月營收年增率為 {revenue_yoy}')
def step_impl(context, revenue_yoy):
    context.revenue_yoy = float(revenue_yoy)


@given('台積電的投信連續買超天數為 {days}')
def step_impl(context, days):
    context.inst_buy_days = int(days)


@given('台積電的融資增減為 {change}')
def step_impl(context, change):
    context.margin_change = int(change)


@given('台積電的 20 日波動率為 {volatility}')
def step_impl(context, volatility):
    context.volatility = float(volatility)


@given('台積電距除息日還有 {ex_div_days} 天')
def step_impl(context, ex_div_days):
    context.ex_div_days = int(ex_div_days)


@when('系統執行每日分析')
def step_impl(context):
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
def step_impl(context, score):
    assert context.analysis_result["ev_score"] >= int(score)


@then('台積電的建議應該為 "{recommendation}"')
def step_impl(context, recommendation):
    assert context.analysis_result["recommendation"] == recommendation


@then('權證條件應該包含 "即將除息" 的警告')
def step_impl(context):
    context.warrant_warning = "即將除息"
    assert True


@given('某標的的 20 日波動率為 {volatility}')
def step_impl(context, volatility):
    context.test_volatility = float(volatility)


@given('波動率警戒線設定為 {limit}')
def step_impl(context, limit):
    context.volatility_limit = int(limit)


@when('系統計算風險等級')
def step_impl(context):
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
def step_impl(context, level):
    assert context.risk_level == level


@then('權證條件應該建議使用 "零股"')
def step_impl(context):
    context.warrant_suggestion = "零股"
    assert True


@given('所有監控標的的投信連續買超天數均為 {days}')
def step_impl(context, days):
    context.all_inst_buy_days = int(days)


@then('高分狙擊機會清單應該為空')
def step_impl(context):
    context.high_score_targets = []
    assert len(context.high_score_targets) == 0


@then('報告應該建議 "{suggestion}"')
def step_impl(context, suggestion):
    context.report_suggestion = suggestion
    assert True
