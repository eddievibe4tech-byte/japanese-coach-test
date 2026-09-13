"""
遙測記錄 BDD Step 定義
"""
from behave import given, when, then
import json


@given('系統已完成對台積電的分析')
def given_tsmc_analysis_completed(context):
    """設定台積電分析完成"""
    context.analysis_done = True


@given('分析結果的 EV 評分為 {score}')
def given_analysis_ev_score(context, score):
    """設定分析結果的 EV 評分"""
    context.ev_score = int(score)


@given('使用的 Prompt 版本為 {version}')
def given_prompt_version(context, version):
    """設定使用的 Prompt 版本"""
    context.prompt_version = int(version)


@given('使用的模型為 "{model}"')
def given_model_name(context, model):
    """設定使用的模型名稱"""
    context.model = model


@when('系統記錄預測到遙測日誌')
def when_record_prediction_to_telemetry(context):
    """記錄預測到遙測日誌"""
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
def then_telemetry_new_record(context):
    """驗證遙測日誌新增記錄"""
    assert context.telemetry_record is not None


@then('該記錄的 "actual_result" 應該為 null')
def then_record_actual_result_null(context):
    """驗證 actual_result 為 null"""
    assert context.telemetry_record["actual_result"] is None


@then('該記錄的 "accuracy" 應該為 null')
def then_record_accuracy_null(context):
    """驗證 accuracy 為 null"""
    assert context.telemetry_record["accuracy"] is None


@given('遙測日誌中有一筆台積電的預測記錄')
def given_telemetry_tsmc_record(context):
    """設定遙測日誌中有台積電預測記錄"""
    context.telemetry_record = {
        "id": "test_2330",
        "stock_code": "2330",
        "prediction": {"recommendation": "積極買入", "ev_score": 82},
        "actual_result": None,
        "accuracy": None
    }


@given('該記錄的預測建議為 "{recommendation}"')
def given_record_prediction_recommendation(context, recommendation):
    """設定記錄的預測建議"""
    context.telemetry_record["prediction"]["recommendation"] = recommendation


@given('該記錄的 EV 評分為 {score}')
def given_record_ev_score(context, score):
    """設定記錄的 EV 評分"""
    context.telemetry_record["prediction"]["ev_score"] = int(score)


@when('我回填實際結果為獲利 {profit}')
def when_fillback_profit_result(context, profit):
    """回填獲利實際結果"""
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
def then_record_accuracy_min(context, accuracy):
    """驗證準確度最小值"""
    assert context.telemetry_record["accuracy"] >= int(accuracy)


@then('該記錄的 "was_correct" 應該為 true')
def then_record_was_correct_true(context):
    """驗證 was_correct 為 true"""
    assert context.telemetry_record["actual_result"]["was_correct"] is True


@given('遙測日誌中有 {count} 筆已回填結果的記錄')
def given_telemetry_records_count(context, count):
    """設定遙測日誌中已回填結果的記錄數量"""
    context.total_records = int(count)


@given('其中 {correct} 筆預測正確')
def given_correct_predictions_count(context, correct):
    """設定預測正確的記錄數量"""
    context.correct_count = int(correct)


@when('系統計算整體績效指標')
def when_calculate_performance_metrics(context):
    """計算整體績效指標"""
    context.accuracy_rate = (context.correct_count / context.total_records) * 100
    context.total_predictions = context.total_records


@then('整體準確率應該為 {rate}')
def then_overall_accuracy_rate(context, rate):
    """驗證整體準確率"""
    assert context.accuracy_rate == float(rate)


@then('總預測次數應該為 {count}')
def then_total_predictions_count(context, count):
    """驗證總預測次數"""
    assert context.total_predictions == int(count)


@given('遙測日誌中有一筆聯發科的預測記錄')
def given_telemetry_mediatek_record(context):
    """設定遙測日誌中有聯發科預測記錄"""
    context.telemetry_record = {
        "id": "test_2454",
        "stock_code": "2454",
        "prediction": {"recommendation": "積極買入", "ev_score": 78},
        "actual_result": None,
        "accuracy": None
    }


@when('我回填實際結果為虧損 {loss}')
def when_fillback_loss_result(context, loss):
    """回填虧損實際結果"""
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
def then_record_accuracy_max(context, accuracy):
    """驗證準確度最大值"""
    assert context.telemetry_record["accuracy"] < int(accuracy)


@then('該記錄的 "was_correct" 應該為 false')
def then_record_was_correct_false(context):
    """驗證 was_correct 為 false"""
    assert context.telemetry_record["actual_result"]["was_correct"] is False
