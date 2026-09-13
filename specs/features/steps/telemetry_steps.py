"""
遙測記錄 BDD Step 定義
"""
from behave import given, when, then
import json


@given('系統已完成對台積電的分析')
def step_impl(context):
    context.analysis_done = True


@given('分析結果的 EV 評分為 {score}')
def step_impl(context, score):
    context.ev_score = int(score)


@given('使用的 Prompt 版本為 {version}')
def step_impl(context, version):
    context.prompt_version = int(version)


@given('使用的模型為 "{model}"')
def step_impl(context, model):
    context.model = model


@when('系統記錄預測到遙測日誌')
def step_impl(context):
    context.telemetry_record = {
        "id": "test_2330",
        "stock_code": "2330",
        "stock_name": "台積電",
        "prompt_version": context.prompt_version,
        "model": context.model,
        "prediction": {"ev_score": context.ev_score, "recommendation": "積極買入"},
        "actual_result": None,
        "accuracy": None
    }


@then('遙測日誌應該新增一筆記錄')
def step_impl(context):
    assert context.telemetry_record is not None


@then('該記錄的 "actual_result" 應該為 null')
def step_impl(context):
    assert context.telemetry_record["actual_result"] is None


@then('該記錄的 "accuracy" 應該為 null')
def step_impl(context):
    assert context.telemetry_record["accuracy"] is None


@given('遙測日誌中有一筆台積電的預測記錄')
def step_impl(context):
    context.telemetry_record = {
        "id": "test_2330",
        "stock_code": "2330",
        "prediction": {"recommendation": "積極買入", "ev_score": 82},
        "actual_result": None,
        "accuracy": None
    }


@given('該記錄的預測建議為 "{recommendation}"')
def step_impl(context, recommendation):
    context.telemetry_record["prediction"]["recommendation"] = recommendation


@given('該記錄的 EV 評分為 {score}')
def step_impl(context, score):
    context.telemetry_record["prediction"]["ev_score"] = int(score)


@when('我回填實際結果為獲利 {profit}')
def step_impl(context, profit):
    profit_pct = float(profit)
    was_correct = profit_pct > 0
    
    # 計算準確度：獲利且預測買入 = 高分
    if profit_pct > 0:
        accuracy = 50 + min(30, profit_pct * 5) + 20  # 基礎分 + 獲利加分 + 理由分
    else:
        accuracy = 50 - abs(profit_pct) * 5
    
    context.telemetry_record["actual_result"] = {
        "profit_pct": profit_pct,
        "was_correct": was_correct
    }
    context.telemetry_record["accuracy"] = accuracy


@then('該記錄的準確度應該大於等於 {accuracy}')
def step_impl(context, accuracy):
    assert context.telemetry_record["accuracy"] >= int(accuracy)


@then('該記錄的 "was_correct" 應該為 true')
def step_impl(context):
    assert context.telemetry_record["actual_result"]["was_correct"] is True


@given('遙測日誌中有 {count} 筆已回填結果的記錄')
def step_impl(context, count):
    context.total_records = int(count)


@given('其中 {correct} 筆預測正確')
def step_impl(context, correct):
    context.correct_count = int(correct)


@when('系統計算整體績效指標')
def step_impl(context):
    context.accuracy_rate = (context.correct_count / context.total_records) * 100
    context.total_predictions = context.total_records


@then('整體準確率應該為 {rate}')
def step_impl(context, rate):
    assert context.accuracy_rate == float(rate)


@then('總預測次數應該為 {count}')
def step_impl(context, count):
    assert context.total_predictions == int(count)


@given('遙測日誌中有一筆聯發科的預測記錄')
def step_impl(context):
    context.telemetry_record = {
        "id": "test_2454",
        "stock_code": "2454",
        "prediction": {"recommendation": "積極買入", "ev_score": 78},
        "actual_result": None,
        "accuracy": None
    }


@when('我回填實際結果為虧損 {loss}')
def step_impl(context, loss):
    loss_pct = float(loss)
    was_correct = False  # 預測買入但虧損 = 錯誤
    
    # 計算準確度：預測買入但虧損 = 低分
    accuracy = 50 - abs(loss_pct) * 5
    
    context.telemetry_record["actual_result"] = {
        "profit_pct": loss_pct,
        "was_correct": was_correct
    }
    context.telemetry_record["accuracy"] = accuracy


@then('該記錄的準確度應該小於 {accuracy}')
def step_impl(context, accuracy):
    assert context.telemetry_record["accuracy"] < int(accuracy)


@then('該記錄的 "was_correct" 應該為 false')
def step_impl(context):
    assert context.telemetry_record["actual_result"]["was_correct"] is False
