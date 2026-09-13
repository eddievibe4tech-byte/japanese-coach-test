"""
狙擊手系統主程式
整合每日分析、風險評估、投資組合優化等功能
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 動態取得專案根目錄 (假設 main.py 在 src/ 下)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
RESULTS_DIR = BASE_DIR / 'results'

# 設定台灣時區 (UTC+8)
TZ_TAIPEI = timezone(timedelta(hours=8))


def setup_logging():
    """設定日誌"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"sniper_system_{datetime.now(TZ_TAIPEI).strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


def ensure_directories():
    """確保必要的目錄存在"""
    for directory in [DATA_DIR, LOGS_DIR, RESULTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def load_config(config_path: str = 'stock_pool.json') -> Dict:
    """載入股票池配置"""
    full_path = DATA_DIR / config_path
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"配置文件 {full_path} 未找到，使用預設配置")
        return {"stocks": [], "sectors": {}}


def append_telemetry(record: Dict):
    """附加一筆預測記錄到 telemetry.json"""
    path = DATA_DIR / 'telemetry.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() \
        else {'records': [], 'metadata': {}}
    data['records'].append(record)
    data['metadata'] = {
        'created_at': data['metadata'].get('created_at') or record['timestamp'],
        'total_records': len(data['records']),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def update_performance_metrics(telemetry_data: Optional[Dict] = None):
    """更新績效指標到 performance_metrics.json"""
    path = DATA_DIR / 'performance_metrics.json'
    
    # 若未提供 telemetry_data，則嘗試讀取現有的
    if telemetry_data is None:
        telemetry_path = DATA_DIR / 'telemetry.json'
        if telemetry_path.exists():
            telemetry_data = json.loads(telemetry_path.read_text(encoding='utf-8'))
        else:
            telemetry_data = {'records': []}
    
    records = telemetry_data.get('records', [])
    
    # 計算總預測數
    total_predictions = len(records)
    
    # 計算已驗證的準確率
    verified_records = [r for r in records if r.get('accuracy') is not None]
    accuracy_rate = 0.0
    if verified_records:
        correct_count = sum(1 for r in verified_records if r.get('accuracy') == 1)
        accuracy_rate = (correct_count / len(verified_records)) * 100
    
    # 計算各版本統計
    version_stats: Dict[str, Dict] = {}
    for record in records:
        version = str(record.get('prompt_version', 1))
        if version not in version_stats:
            version_stats[version] = {'version': int(version), 'predictions': 0, 'correct': 0}
        version_stats[version]['predictions'] += 1
        if record.get('accuracy') == 1:
            version_stats[version]['correct'] += 1
    
    # 計算各版本準確率
    version_stats_list = []
    for version, stats in version_stats.items():
        stats['accuracy'] = round((stats['correct'] / stats['predictions']) * 100, 1) if stats['predictions'] > 0 else 0.0
        version_stats_list.append(stats)
    
    now = datetime.now(TZ_TAIPEI)
    metrics = {
        'total_predictions': total_predictions,
        'accuracy_rate': round(accuracy_rate, 1),
        'current_version': max(int(v) for v in version_stats.keys()) if version_stats else 1,
        'last_updated': now.isoformat(),
        'version_stats': version_stats_list
    }
    
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"績效指標已更新：總預測={total_predictions}, 準確率={accuracy_rate:.1f}%")


def run_daily_analysis(mode: str = 'full') -> Dict:
    """
    執行每日盤後分析
    
    Args:
        mode: 分析模式 ('full', 'analysis', 'risk', 'optimize')
    
    Returns:
        分析結果字典
    """
    from src.finmind_client import FinMindClient
    from src.groq_client import GroqClient
    from src.risk_calculator import calculate_volatility, assess_risk_level
    
    logger.info(f"開始執行每日分析，模式：{mode}")
    
    # 使用台灣時間
    now = datetime.now(TZ_TAIPEI)
    results = {
        'timestamp': now.isoformat(),
        'mode': mode,
        'status': 'success',
        'data': {}
    }
    
    config = load_config()
    stocks = config.get('stocks', [])
    
    if mode in ['full', 'analysis'] and stocks:
        logger.info("執行市場體制與個股分析...")
        
        finmind = FinMindClient()  # 自動讀 FINMIND_API_TOKEN
        groq = GroqClient()        # 自動讀 GROQ_API_KEY
        
        # 讀取分析 Prompt 模板
        prompt_path = BASE_DIR / 'prompts' / 'main_analysis.txt'
        try:
            prompt_tpl = prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.warning("Prompt 模板未找到，使用預設模板")
            prompt_tpl = "請分析以下股票數據並輸出 JSON：{{\"ev_score\": 50, \"recommendation\": \"觀望\", \"reason\": \"數據不足\"}}"
        
        regime = '震盪'  # 進階可改呼叫 groq.judge_regime(market_data)
        
        all_results = []
        for stock in stocks:
            code = stock['code']
            try:
                prices = finmind.get_stock_price(code) or []
                revenue = finmind.get_revenue(code) or {}
                stock_data = {
                    'code': code,
                    'name': stock['name'],
                    'industry': stock.get('industry', ''),
                    'regime': regime,
                    'revenue_yoy': revenue.get('yoy_growth', 0),
                    'inst_buy_days': finmind.get_institutional_buy(code) or 0,
                    'margin_change': finmind.get_margin_balance(code) or 0,
                    'change_5d': round((prices[-1] / prices[-6] - 1) * 100, 2) if len(prices) >= 6 else 0.0,
                    'volatility': calculate_volatility(prices),
                    'ex_div_days': '-',
                }
                
                analysis = groq.analyze_stock(prompt_tpl, stock_data) or {}
                record = {**stock_data, **analysis,
                          'risk_level': assess_risk_level(stock_data['volatility'])}
                all_results.append(record)
                
                # 寫入 telemetry
                append_telemetry({
                    'id': f"{now.strftime('%Y%m%d')}-{code}",
                    'timestamp': now.isoformat(),
                    'stock_code': code,
                    'stock_name': stock['name'],
                    'prompt_version': 1,
                    'model': groq.model,
                    'regime': regime,
                    'input': stock_data,
                    'prediction': analysis,
                    'actual_result': None,  # 待回填
                    'accuracy': None,       # 待回填
                })
                
                logger.info(f"{code} 分析完成：EV={analysis.get('ev_score')}")
                
            except Exception as e:
                logger.error(f"分析 {code} 失敗：{e}")
        
        # 寫入 deep_analysis.json
        deep = {
            'analyzed_at': now.isoformat(),
            'regime': regime,
            'high_score_targets': [r for r in all_results if (r.get('ev_score') or 0) >= 70],
            'all_results': all_results
        }
        (DATA_DIR / 'deep_analysis.json').write_text(
            json.dumps(deep, ensure_ascii=False, indent=2), encoding='utf-8')
        
        results['data']['stock_analysis'] = deep
        logger.info(f"深度分析結果已儲存，共分析 {len(all_results)} 檔股票")
    
    if mode in ['full', 'risk']:
        logger.info("執行風險評估...")
        # TODO: 呼叫風險計算器
        
    if mode in ['full', 'optimize']:
        logger.info("檢查是否需要優化 Prompt...")
        # TODO: 呼叫 Prompt Optimizer
    
    # 更新績效指標
    update_performance_metrics()
    
    # 儲存結果 (使用台灣時間命名)
    output_file = RESULTS_DIR / f"analysis_{now.strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"分析結果已儲存至 {output_file}")
    except Exception as e:
        logger.error(f"儲存結果失敗：{e}")
        results['status'] = 'partial'
    
    return results


def main():
    """主程式進入點"""
    parser = argparse.ArgumentParser(description='狙擊手系統主程式')
    parser.add_argument(
        '--mode',
        type=str,
        default='full',
        choices=['full', 'analysis', 'risk', 'optimize'],
        help='執行模式：full(完整), analysis(僅分析), risk(僅風險), optimize(僅優化)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='stock_pool.json',
        help='配置文件路徑'
    )
    
    args = parser.parse_args()
    
    # 設定日誌
    setup_logging()
    
    # 確保目錄存在
    ensure_directories()
    
    # 載入配置
    config = load_config(args.config)
    
    # 執行分析
    results = run_daily_analysis(mode=args.mode)
    
    # 輸出結果摘要 (供 GitHub Actions Log 查看)
    print("\n" + "="*50)
    print("狙擊手系統執行完成")
    print(f"時間：{results['timestamp']}")
    print(f"狀態：{results['status']}")
    print("="*50 + "\n")
    
    return 0 if results['status'] == 'success' else 1


if __name__ == '__main__':
    exit(main())
