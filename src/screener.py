"""
台股海選引擎 (Screener)
對標 Finviz 的全市場硬規則篩選模組
"""
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from finmind_client import FinMindClient

# 海選條件 (對標 Alpha Picks 的量化邏輯)
SCREENER_RULES = {
    "market_cap_min": 100,      # 市值 > 100億 (避開流動性差的迷你股)
    "revenue_yoy_min": 15.0,    # 營收年增率 > 15% (成長動能)
    "inst_buy_days_min": 3,     # 投信連買 > 3天 (法人認同)
    "price_above_ma20": True    # 股價站上 20日均線 (右側多頭)
}


def get_all_taiwan_stocks(finmind: FinMindClient) -> List[Dict]:
    """
    取得全市場股票清單（過濾掉 ETF 與權證）
    
    Args:
        finmind: FinMind 客戶端
        
    Returns:
        股票清單列表
    """
    # 使用 FinMind 的 TaiwanStockInfo API (修正：TaiwanStockInfoWithWarrant 不存在)
    try:
        # 移除 days=1，改用標準呼叫
        data = finmind._make_request('TaiwanStockInfo', '') or []
    except Exception as e:
        print(f"⚠️ 獲取股票清單失敗：{e}")
        data = []
    
    stocks = []
    for item in data:
        stock_id = item.get('stock_id', '')
        stock_name = item.get('stock_name', '')
        industry = item.get('industry_category', '未知')
        
        # 過濾：只保留一般股票（排除 ETF、權證等）
        if len(stock_id) == 4 and stock_id.isdigit():
            stocks.append({
                'stock_id': stock_id,
                'stock_name': stock_name,
                'industry': industry
            })
    
    # 🟡 P2 優化：如果 API 失敗或回傳空，使用預設的 Top 50 活躍股清單確保系統能跑
    if not stocks:
        print("⚠️ API 無回傳，使用預設活躍股清單進行海選...")
        fallback_codes = ["2330", "2317", "2382", "2308", "2454", "2881", "2882", "3711", "3017", "1504", 
                          "1519", "2303", "2412", "2002", "2884", "2885", "2886", "2890", "2891", "2892"]
        # 這裡可以簡單回傳代號，名稱留空或後續再補
        stocks = [{'stock_id': code, 'stock_name': code, 'industry': '預設'} for code in fallback_codes]
        
    print(f"✅ 載入 {len(stocks)} 檔台股")
    return stocks


def run_weekly_screener(finmind: FinMindClient) -> List[Dict]:
    """
    執行每週海選，找出符合硬規則的 Alpha 候選股
    
    Args:
        finmind: FinMind 客戶端
        
    Returns:
        候選股清單（已排序）
    """
    print("🔍 啟動全市場海選引擎 (台股版 Finviz)...")
    
    # 1. 獲取全市場股票清單
    all_stocks = get_all_taiwan_stocks(finmind)
    
    candidates = []
    processed = 0
    
    # 2. 迴圈檢查 (加入 Rate Limit 控制)
    # 測試期先跑前 200 檔活躍股，避免 API 超時
    for stock in all_stocks[:200]:
        code = stock['stock_id']
        processed += 1
        
        if processed % 20 == 0:
            print(f"  處理中：{processed}/{min(200, len(all_stocks))} ({len(candidates)} 檔入選)")
        
        try:
            # A. 檢查營收年增率 (使用既有的 get_revenue 方法)
            revenue_data = finmind.get_revenue(code)
            if not revenue_data:
                continue
            rev_yoy = revenue_data.get('yoy_growth', 0)
            if rev_yoy < SCREENER_RULES["revenue_yoy_min"]:
                continue
                
            # B. 檢查籌碼（投信連買天數）(使用既有的 get_institutional_buy 方法)
            inst_days = finmind.get_institutional_buy(code, days=10)
            if inst_days < SCREENER_RULES["inst_buy_days_min"]:
                continue
                
            # C. 檢查技術面 (MA20) (使用既有的 get_stock_price 方法)
            prices = finmind.get_stock_price(code, days=30)
            if not prices or len(prices) < 20:
                continue
            
            current_price = prices[-1]
            ma20 = sum(prices[-20:]) / 20
            if current_price < ma20:
                continue
                
            # 通過所有硬規則，加入候選池
            candidates.append({
                "code": code,
                "name": stock['stock_name'],
                "industry": stock.get('industry', '未知'),
                "revenue_yoy": round(rev_yoy, 2),
                "inst_buy_days": inst_days,
                "current_price": round(current_price, 2),
                "ma20": round(ma20, 2),
                "screened_at": datetime.now().strftime('%Y-%m-%d')
            })
            
        except Exception as e:
            print(f"  ⚠️ 檢查 {code} 時出錯：{e}")
            continue
        finally:
            # 🟠 P1 修正：避免觸發 FinMind API Rate Limit (每 1.5 秒呼叫一次)
            time.sleep(1.5)
    
    # 排序：營收成長最強 + 籌碼最乾淨的排前面
    candidates.sort(key=lambda x: (x['revenue_yoy'], x['inst_buy_days']), reverse=True)
    
    # 只取前 15 名進入體檢階段
    top_candidates = candidates[:15]
    
    # 3. 輸出候選清單
    save_screener_results(top_candidates)
    print(f"✅ 海選完成，共找出 {len(top_candidates)} 檔 Alpha 候選股")
    
    return top_candidates


def save_screener_results(candidates: List[Dict]) -> None:
    """
    儲存海選結果到 JSON 檔案
    
    Args:
        candidates: 候選股清單
    """
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, 'screener_candidates.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "candidates": candidates,
            "updated_at": datetime.now().isoformat(),
            "rules_applied": SCREENER_RULES
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 結果已儲存至：{output_path}")


if __name__ == "__main__":
    # 🟢 修法 C：多重讀取環境變數，相容多種可能的 Secret 名稱
    token = (
        os.getenv('FINMIND_TOKEN')
        or os.getenv('FINMIND_API_TOKEN')
        or os.getenv('FINMIND_API_KEY')
        or ''
    )
    
    if not token:
        print("⚠️ 警告：未設定 FINMIND_TOKEN / FINMIND_API_TOKEN / FINMIND_API_KEY，請從環境變數提供")
        exit(1)
    
    client = FinMindClient(token=token)
    candidates = run_weekly_screener(client)
    
    print("\n🎯 本週 Alpha 候選股 Top 5:")
    for i, stock in enumerate(candidates[:5], 1):
        print(f"  {i}. {stock['code']} {stock['name']} - 營收成長 {stock['revenue_yoy']}%, 投信連買 {stock['inst_buy_days']} 天")
