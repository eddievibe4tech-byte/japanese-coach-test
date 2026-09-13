"""
風險評估 BDD Step 定義
"""
from behave import given, when, then


@given('監控池中有以下股票')
def step_impl(context):
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
    context.test_stocks = stocks


@given('產業集中度上限為 {limit}')
def step_impl(context, limit):
    context.industry_limit = int(limit)


@when('系統執行風險評估')
def step_impl(context):
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
def step_impl(context, score):
    assert context.risk_score >= int(score)


@then('警告訊息應該包含 "{message}"')
def step_impl(context, message):
    assert any(message in w for w in context.warnings)


@then('風險狀態應該為 "{status}"')
def step_impl(context, status):
    assert context.risk_status == status


@then('建議動作應該為 "{suggestion}"')
def step_impl(context, suggestion):
    assert context.suggestion == suggestion


@then('風險分數應該小於等於 {score}')
def step_impl(context, score):
    assert context.risk_score <= int(score)
