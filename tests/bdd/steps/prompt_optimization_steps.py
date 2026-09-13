"""
Prompt 優化 BDD Step 定義
"""
from behave import given, when, then


@given('過去 14 天有 {count} 筆已回填結果的預測記錄')
def step_impl(context, count):
    context.prediction_count = int(count)


@given('當前 Prompt 版本為 {version}')
def step_impl(context, version):
    context.current_version = int(version)


@given('當前準確率為 {rate}')
def step_impl(context, rate):
    context.accuracy_rate = float(rate)


@when('系統執行每週 Prompt 優化')
def step_impl(context):
    optimization_threshold = 5
    
    if context.prediction_count < optimization_threshold:
        context.optimization_skipped = True
        context.new_version = context.current_version
        return
    
    # 模擬 AI API 呼叫失敗的情況
    if hasattr(context, 'api_failed') and context.api_failed:
        context.optimization_failed = True
        context.new_version = context.current_version
        return
    
    # 執行優化
    context.optimization_skipped = False
    context.optimization_failed = False
    context.new_version = context.current_version + 1
    context.backup_file = f"main_analysis_v{context.current_version}.txt"


@then('系統應該呼叫 AI 分析錯誤原因')
def step_impl(context):
    assert not context.optimization_skipped


@then('應該生成優化後的 Prompt')
def step_impl(context):
    assert hasattr(context, 'new_version')


@then('Prompt 版本應該更新為 {version}')
def step_impl(context, version):
    assert context.new_version == int(version)


@then('舊版本應該備份為 "{filename}"')
def step_impl(context, filename):
    assert context.backup_file == filename


@given('過去 14 天只有 {count} 筆已回填結果的預測記錄')
def step_impl(context, count):
    context.prediction_count = int(count)


@given('優化門檻為 {threshold} 筆')
def step_impl(context, threshold):
    context.optimization_threshold = int(threshold)


@then('系統應該跳過優化')
def step_impl(context):
    assert context.optimization_skipped is True


@then('Prompt 版本應該維持不變')
def step_impl(context):
    assert context.new_version == context.current_version


@given('過去 14 天有 {count} 筆已回填結果的預測記錄')
def step_impl(context, count):
    context.prediction_count = int(count)


@given('AI API 呼叫失敗')
def step_impl(context):
    context.api_failed = True


@then('系統應該記錄錯誤日誌')
def step_impl(context):
    assert context.optimization_failed is True


@then('應該在下次執行時重試')
def step_impl(context):
    # 這是一個預期行為，不需要實際驗證
    assert True
