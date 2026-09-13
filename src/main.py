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

# 🔴 最佳實踐：將 Import 移到檔案頂端
from src.finmind_client import FinMindClient
from src.groq_client import GroqClient
from src.risk_calculator import calculate_volatility, assess_risk_level
from src.yahoo_client import YahooFinanceClient


def auto_verify_predictions(telemetry_data: Dict, finmind: FinMindClient, horizon: int = 5) -> int:
    """
    🔴 P0 修正：自動回填驗證
    
    自動回填：預測滿 horizon 個交易日後，
    用「預測當日收盤價 vs 現在價」計算實際報酬與對錯。
    
    Args:
        telemetry_data: 遙測數據字典
        finmind: FinMind 客戶端
        horizon: 驗證天數（預設 5 交易日）
        
    Returns:
        已驗證的記錄數量
    """
    from datetime import datetime
    now = datetime.now(TZ_TAIPEI)
    verified = 0

    for rec in telemetry_data.get("records", []):
        # 跳過已驗證的記錄
        if rec.get("actual_result"):
            continue
        
        entry_price = rec.get("entry_price")
        if not entry_price:
            continue

        pred_dt = datetime.fromisoformat(rec["timestamp"].replace('+08:00', '+08:00'))
        # 簡化：用日曆日 * 1.5 近似交易日
        days_elapsed = (now - pred_dt).days
        if days_elapsed < int(horizon * 1.5):
            continue

        # 取得當前價格
        try:
            prices = finmind.get_stock_price(rec["stock_code"], days=1)
            if not prices:
                continue
            current = prices[-1]
        except Exception:
            continue

        # 計算報酬率
        ret = round((current - entry_price) / entry_price * 100, 2)
        rec_pred = rec.get("prediction", {}).get("recommendation", "")

        # 判斷對錯
        if rec_pred in ("積極買入", "謹慎買入"):
            correct = ret > 0
        elif rec_pred == "避開":
            correct = ret <= 0  # 避開後真的沒漲＝正確
        else:  # 回檔觀察/觀望
            correct = abs(ret) < 3

        rec["actual_result"] = {
            "profit_pct": ret,
            "was_correct": correct,
            "horizon_days": horizon,
            "auto": True,
            "verified_at": now.isoformat()
        }
        rec["accuracy"] = 1 if correct else 0
        verified += 1

    return verified

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
    """設定日誌 (🟡 修正：避免重複設定 Handler)"""
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()  # 清除舊的 Handler
    
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


def update_performance_metrics(telemetry_data: Optional[Dict] = None):
    """更新績效指標到 performance_metrics.json"""
    path = DATA_DIR / 'performance_metrics.json'
    
    # 若未提供 telemetry_data，則嘗試讀取現有的
    if telemetry_data is None:
        telemetry_path = DATA_DIR / 'telemetry.json'
        if telemetry_path.exists():
            telemetry_data = json.loads(telemetry_path.read_text(encoding='utf-8'))
        else:
            telemetry_data = {'records': [], 'metadata': {}}
    
    records = telemetry_data.get('records', [])
    total_predictions = len(records)
    
    # 計算已驗證的準確率
    verified_records = [r for r in records if r.get('accuracy') is not None]
    verified_count = len(verified_records)
    
    # 🟡 P0 修正：驗證數 < 10 時顯示「資料不足」，不顯示 0.0%
    accuracy_rate = None
    accuracy_display = "資料不足"
    if verified_count >= 10:
        correct_count = sum(1 for r in verified_records if r.get('accuracy') == 1)
        accuracy_rate = (correct_count / verified_count) * 100
        accuracy_display = round(accuracy_rate, 1)
    elif verified_count > 0:
        accuracy_display = f"已驗證 {verified_count}/{total_predictions}"
    
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
        if stats['predictions'] > 0:
            stats['accuracy'] = round((stats['correct'] / stats['predictions']) * 100, 1)
        else:
            stats['accuracy'] = None
        version_stats_list.append(stats)
    
    now = datetime.now(TZ_TAIPEI)
    metrics = {
        'total_predictions': total_predictions,
        'verified_count': verified_count,
        'accuracy_rate': accuracy_display,
        'current_version': max(int(v) for v in version_stats.keys()) if version_stats else 1,
        'last_updated': now.isoformat(),
        'version_stats': version_stats_list
    }
    
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"績效指標已更新：總預測={total_predictions}, 已驗證={verified_count}, 準確率={accuracy_display}")


def run_daily_analysis(mode: str = 'full') -> Dict:
    """
    執行每日盤後分析
    
    Args:
        mode: 分析模式 ('full', 'analysis', 'risk', 'optimize')
    
    Returns:
        分析結果字典
    """
    logger.info(f"開始執行每日分析，模式：{mode}")
    
    # 🔴 P0 修正：執行分析前先自動回填驗證
    telemetry_path = DATA_DIR / 'telemetry.json'
    if telemetry_path.exists():
        telemetry_data = json.loads(telemetry_path.read_text(encoding='utf-8'))
        finmind = FinMindClient()
        verified_count = auto_verify_predictions(telemetry_data, finmind)
        if verified_count > 0:
            telemetry_path.write_text(json.dumps(telemetry_data, ensure_ascii=False, indent=2), encoding='utf-8')
            logger.info(f"自動驗證完成：已更新 {verified_count} 筆預測")
            # 更新績效指標
            update_performance_metrics(telemetry_data)
    
    # 使用台灣時間
    now = datetime.now(TZ_TAIPEI)
    results = {
        'timestamp': now.isoformat(),
        'mode': mode,
        'status': 'success',
        'data': {}
    }
    
    if mode in ['full', 'analysis']:
        logger.info("執行市場體制與個股分析...")
        
        # 🔴 修正：批次處理 telemetry (效能優化)
        config = load_config()
        stocks = config.get('stocks', [])
        
        # 讀取當前 Prompt 版本 (🔴 修正：不再硬編碼為 1)
        history_path = DATA_DIR / 'prompt_history.json'
        history = json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else {}
        current_prompt_version = history.get('current_version', 1)
        
        # 🔴 修正：批次讀取 telemetry (避免頻繁 I/O)
        telemetry_path = DATA_DIR / 'telemetry.json'
        telemetry_data = json.loads(telemetry_path.read_text(encoding='utf-8')) if telemetry_path.exists() else {'records': [], 'metadata': {}}
        
        all_results = []
        failed_count = 0
        
        if stocks:
            finmind = FinMindClient()
            groq = GroqClient()
            yahoo = YahooFinanceClient()  # ✅ 初始化備援客戶端
            prompt_tpl = (BASE_DIR / 'prompts' / 'main_analysis.txt').read_text(encoding='utf-8')
            regime = '震盪'  # 進階可改呼叫 groq.judge_regime(market_data)
            
            for stock in stocks:
                code = stock['code']
                try:
                    # ✅ 1. 初始化所有變數為安全預設值
                    prices = []
                    revenue_yoy = 0.0
                    gross_margin = 0.0
                    net_margin = 0.0
                    eps = 0.0
                    inst_buy_days = 0
                    margin_change = 0
                    ma5, ma20, rsi, macd = 0.0, 0.0, 50.0, 0.0
                    price_above_ma20 = False
                    change_5d = 0.0
                    volatility = 0.0
                    use_yahoo_fallback = False
                    
                    # ✅ 2. 嘗試使用 FinMind (主力)
                    try:
                        prices = finmind.get_stock_price(code) or []
                        revenue = finmind.get_revenue(code) or {}
                        revenue_yoy = revenue.get('yoy_growth', 0.0)
                        
                        # 財報數據
                        try:
                            financials = finmind.get_financial_statements(code) or {}
                            gross_margin = financials.get('gross_margin', 0.0)
                            net_margin = financials.get('net_margin', 0.0)
                            eps = financials.get('eps', 0.0)
                        except Exception as e:
                            logger.warning(f"{code} 財報數據抓取失敗，使用預設值：{e}")
                        
                        # 技術指標
                        try:
                            tech = finmind.get_technical_indicators(code) or {}
                            ma5 = tech.get('ma5', 0.0)
                            ma20 = tech.get('ma20', 0.0)
                            rsi = tech.get('rsi', 50.0)
                            macd = tech.get('macd', 0.0)
                            price_above_ma20 = tech.get('price_above_ma20', False)
                        except Exception as e:
                            logger.warning(f"{code} 技術指標計算失敗：{e}")
                        
                        # ✅ 關鍵：在這裡一次性取得籌碼數據，避免後續重複呼叫 API
                        inst_buy_days = finmind.get_institutional_buy(code) or 0
                        margin_change = finmind.get_margin_balance(code) or 0
                        
                        logger.info(f"{code}: 使用 FinMind 數據成功")
                        
                    except Exception as e:
                        # ✅ 3. FinMind 失敗，切換到 Yahoo (備援)
                        logger.warning(f"{code}: FinMind 失敗 ({e})，切換至 Yahoo Finance 備援")
                        use_yahoo_fallback = True
                        
                        yahoo_data = yahoo.get_stock_data(code)
                        if yahoo_data:
                            prices = yahoo_data['prices']
                            # 直接使用 Yahoo 算好的指標，避免重複計算
                            change_5d = yahoo_data['change_5d']
                            volatility = yahoo_data['volatility']
                            ma5 = yahoo_data['ma5']
                            ma20 = yahoo_data['ma20']
                            rsi = yahoo_data['rsi']
                            macd = yahoo_data['macd']
                            price_above_ma20 = yahoo_data['price_above_ma20']
                            
                            logger.info(f"{code}: Yahoo Finance 備援成功")
                        else:
                            raise Exception("Yahoo Finance 備援也失敗，無歷史數據")
                    
                    # ✅ 4. 若使用 FinMind 成功，且尚未計算 change_5d 與 volatility，則在此計算
                    if not use_yahoo_fallback:
                        change_5d = round((prices[-1] / prices[-6] - 1) * 100, 2) if (len(prices) >= 6 and prices[-6] != 0) else 0.0
                        volatility = calculate_volatility(prices)

                    # ✅ 5. 組裝最終的 stock_data（加入 data_source 標記）
                    stock_data = {
                        'code': code,
                        'name': stock['name'],
                        'industry': stock.get('industry', ''),
                        'regime': regime,
                        'revenue_yoy': revenue_yoy,
                        'gross_margin': gross_margin,
                        'net_margin': net_margin,
                        'eps': eps,
                        'inst_buy_days': inst_buy_days,
                        'margin_change': margin_change,
                        'change_5d': change_5d,
                        'volatility': volatility,
                        'ma5': ma5,
                        'ma20': ma20,
                        'rsi': rsi,
                        'macd': macd,
                        'price_above_ma20': price_above_ma20,
                        'current_price': float(prices[-1]) if prices else 0.0,
                        'data_source': 'yahoo' if use_yahoo_fallback else 'finmind',  # ✅ 加入數據來源標記
                    }
                    
                    # ✅ 6. 呼叫 Groq 分析 (加入容錯)
                    analysis = groq.analyze_stock(prompt_tpl, stock_data)
                    if not analysis:
                        logger.warning(f"{code} AI 分析失敗，使用預設值")
                        analysis = {
                            'ev_score': 50,
                            'recommendation': '觀望',
                            'reason': f"AI 分析失敗，請手動檢視 {stock['name']} 數據"
                        }
                    
                    record = {**stock_data, **analysis, 'risk_level': assess_risk_level(volatility)}
                    all_results.append(record)

                    # ✅ 7. 記憶體中 Append
                    # 🔴 修正：prediction 應該包含完整的分析結果，而不只是 AI 回應
                    # 這樣儀表板才能正確顯示股票代碼、名稱、建議等資訊
                    prediction_record = {
                        'ev_score': analysis.get('ev_score') if analysis else None,
                        'recommendation': analysis.get('recommendation') if analysis else '-',
                        'reason': analysis.get('reason') if analysis else 'AI 分析失敗',
                        # 加入完整的股票數據供儀表板使用
                        'stock_code': code,
                        'stock_name': stock['name'],
                        'industry': stock_data.get('industry', '-'),
                        'close_price': prices[-1] if prices else None,
                        'change_5d': stock_data.get('change_5d', None),
                        'volatility': stock_data.get('volatility', None),
                        'rsi': stock_data.get('rsi', None),
                    }
                    
                    telemetry_data['records'].append({
                        'id': f"{now.strftime('%Y%m%d')}-{code}",
                        'timestamp': now.isoformat(),
                        'stock_code': code,
                        'stock_name': stock['name'],
                        'prompt_version': current_prompt_version,
                        'model': groq.model,
                        'regime': regime,
                        'input': stock_data,
                        'prediction': prediction_record,
                        'actual_result': None,
                        'accuracy': None,
                        # 🔴 P0 修正：記錄 entry_price 供自動驗證使用
                        'entry_price': prices[-1] if prices else None,
                    })
                    logger.info(f"{code} 分析完成：EV={analysis.get('ev_score') if analysis else 'N/A'}")
                    
                except Exception as e:
                    logger.error(f"分析 {code} 完全失敗：{e}")
                    failed_count += 1
            
            # 🔴 修正：一次性寫入 telemetry (批次處理)
            if 'metadata' not in telemetry_data:
                telemetry_data['metadata'] = {}
            
            telemetry_data['metadata']['created_at'] = telemetry_data['metadata'].get('created_at') or now.isoformat()
            telemetry_data['metadata']['total_records'] = len(telemetry_data['records'])
            telemetry_path.write_text(json.dumps(telemetry_data, ensure_ascii=False, indent=2), encoding='utf-8')
            
            # 🔴 修正：呼叫績效指標更新函數
            update_performance_metrics(telemetry_data)
            
            # 🟡 修正：狀態判定更嚴謹
            if failed_count > 0:
                results['status'] = 'partial'
                logger.warning(f"部分股票分析失敗：成功 {len(all_results)}/{len(stocks)}")
            
            deep = {'analyzed_at': now.isoformat(), 'regime': regime,
                    'high_score_targets': [r for r in all_results if (r.get('ev_score') or 0) >= 70],
                    'all_results': all_results}
            (DATA_DIR / 'deep_analysis.json').write_text(
                json.dumps(deep, ensure_ascii=False, indent=2), encoding='utf-8')
            results['data']['stock_analysis'] = deep
        
    if mode in ['full', 'risk']:
        logger.info("執行風險評估...")
        # TODO: 呼叫風險計算器
        
    if mode in ['full', 'optimize']:
        logger.info("檢查是否需要優化 Prompt...")
        # TODO: 呼叫 Prompt Optimizer

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
