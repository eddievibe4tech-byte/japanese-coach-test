"""
Behave 環境設定
在每個測試場景前後執行初始化和清理
"""
import os
import sys
import json
import tempfile
import shutil

# 將 src 加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def before_all(context):
    """所有測試開始前執行"""
    context.temp_dir = tempfile.mkdtemp()
    context.data_dir = os.path.join(context.temp_dir, 'data')
    os.makedirs(context.data_dir, exist_ok=True)
    
    # 建立臨時的資料文件
    _create_temp_data_files(context)


def after_all(context):
    """所有測試結束後執行"""
    if hasattr(context, 'temp_dir') and os.path.exists(context.temp_dir):
        shutil.rmtree(context.temp_dir)


def before_scenario(context, scenario):
    """每個場景開始前執行 - 初始化 Context 狀態"""
    # 重置臨時數據
    _create_temp_data_files(context)
    
    # 統一初始化 Context 狀態，避免殘留
    context.prediction_count = 0
    context.current_version = 1
    context.api_failed = False
    context.optimization_skipped = False
    context.optimization_failed = False
    context.new_version = None
    context.backup_file = None
    context.accuracy_rate = None
    context.optimization_threshold = 5


def _create_temp_data_files(context):
    """建立臨時測試數據"""
    # 預設的體制設定
    regime_config = {
        "current_regime": "震盪",
        "trade_size": 5000,
        "target_rr": 2,
        "max_positions": 3,
        "max_risk_percent": 2,
        "industry_limit_percent": 40,
        "leverage_limit": 5,
        "volatility_limit": 30,
        "last_updated": ""
    }
    
    with open(os.path.join(context.data_dir, 'regime.json'), 'w', encoding='utf-8') as f:
        json.dump(regime_config, f, ensure_ascii=False, indent=2)
    
    # 預設的監控池
    stock_pool = {
        "stocks": [
            {"code": "2330", "name": "台積電", "industry": "半導體", "topic": "AI", "ex_div_date": "", "notes": ""},
            {"code": "2308", "name": "台達電", "industry": "電子", "topic": "AI 電源", "ex_div_date": "", "notes": ""},
            {"code": "2881", "name": "富邦金", "industry": "金融", "topic": "高利率", "ex_div_date": "", "notes": ""}
        ]
    }
    
    with open(os.path.join(context.data_dir, 'stock_pool.json'), 'w', encoding='utf-8') as f:
        json.dump(stock_pool, f, ensure_ascii=False, indent=2)
    
    # 預設的遙測記錄
    telemetry = {"records": [], "metadata": {"created_at": "", "total_records": 0}}
    
    with open(os.path.join(context.data_dir, 'telemetry.json'), 'w', encoding='utf-8') as f:
        json.dump(telemetry, f, ensure_ascii=False, indent=2)
