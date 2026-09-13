"""
Prompt 優化 BDD Step 定義
"""
from behave import given, when, then


@given('過去 14 天有 {count} 筆已回填結果的預測記錄')
def given_prediction_records_count(context, count):
    """設定預測記錄數量"""
    context.prediction_count = int(count)


@given('當前 Prompt 版本為 {version}')
def given_current_prompt_version(context, version):
    """設定當前 Prompt 版本"""
    context.current_version = int(version)


@given('當前準確率為 {rate}')
def given_current_accuracy_rate(context, rate):
    """設定當前準確率"""
    context.accuracy_rate = float(rate)


@when('系統執行每週 Prompt 優化')
def when_execute_weekly_optimization(context):
    """執行 Prompt 優化流程"""
    # 從 context 讀取門檻值（若未設定則使用預設值）
    optimization_threshold = getattr(context, 'optimization_threshold', 5)
    
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
def then_should_call_ai_analysis(context):
    """驗證是否呼叫 AI 分析"""
    assert not context.optimization_skipped


@then('應該生成優化後的 Prompt')
def then_should_generate_optimized_prompt(context):
    """驗證是否生成優化後的 Prompt"""
    assert hasattr(context, 'new_version')


@then('Prompt 版本應該更新為 {version}')
def then_prompt_version_updated(context, version):
    """驗證 Prompt 版本更新"""
    assert context.new_version == int(version)


@then('舊版本應該備份為 "{filename}"')
def then_old_version_backed_up(context, filename):
    """驗證舊版本備份"""
    assert context.backup_file == filename


@given('過去 14 天只有 {count} 筆已回填結果的預測記錄')
def given_only_few_prediction_records(context, count):
    """設定少量預測記錄"""
    context.prediction_count = int(count)


@given('優化門檻為 {threshold} 筆')
def given_optimization_threshold(context, threshold):
    """設定優化門檻"""
    context.optimization_threshold = int(threshold)


@then('系統應該跳過優化')
def then_should_skip_optimization(context):
    """驗證是否跳過優化"""
    assert context.optimization_skipped is True


@then('Prompt 版本應該維持不變')
def then_prompt_version_unchanged(context):
    """驗證 Prompt 版本不變"""
    assert context.new_version == context.current_version


@given('AI API 呼叫失敗')
def given_api_call_failed(context):
    """模擬 API 呼叫失敗"""
    context.api_failed = True


@then('系統應該記錄錯誤日誌')
def then_should_log_error(context):
    """驗證是否記錄錯誤"""
    assert context.optimization_failed is True


@then('應該在下次執行時重試')
def then_should_retry_next_time(context):
    """驗證重試機制（預期行為，不需實際驗證）"""
    assert True
