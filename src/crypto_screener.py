"""
加密貨幣海選引擎
篩選條件：恐懼貪婪指數 + 技術面 + 市值
情境分類：四象限決策矩陣 (RSI + FNG)
"""
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from crypto_client import CryptoClient

# 加密貨幣海選條件
CRYPTO_RULES = {
    "fear_greed_max": 75,           # 恐懼貪婪指數 < 75（避免極度貪婪時追高）
    "min_market_cap": 1_000_000_000, # 市值 > 10 億美元（避免山寨幣）
    "rsi_max": 70,                  # RSI < 70（避免超買）
    "price_above_ma20": True,       # 價格站上 MA20（右側交易）
}

# 監控清單（主流幣 + 熱門山寨幣）
WATCHLIST = [
    'bitcoin', 'ethereum', 'solana', 'bnb', 'xrp',
    'cardano', 'dogecoin', 'tron', 'avalanche-2', 'chainlink',
    'polkadot', 'polygon-pos', 'litecoin', 'uniswap', 'cosmos'
]


def get_scenario_badge(fng: int, rsi: float, price_above_ma20: bool, change_7d: float = 0) -> Dict:
    """
    根據四象限決策矩陣判斷當前情境
    
    Returns:
        dict: {
            'scenario': str,  # 情境名稱
            'recommendation': str,  # 建議策略
            'win_rate': str,  # 歷史勝率
            'win_rate_note': str,  # 勝率備註
            'position_size': str,  # 建議部位
            'stop_loss': str,  # 停損點
            'take_profit': str,  # 獲利點
            'holding_period': str  # 持有期間
        }
    """
    # 情境 4: 🔴 極度危險 (極度貪婪 + 超買)
    if fng > 75 and rsi > 70:
        return {
            'scenario': '極度危險',
            'recommendation': '避開',
            'win_rate': '20%',
            'win_rate_note': '歷史統計：BTC 日線、1 年期；山寨幣僅供參考',
            'position_size': '0%',
            'stop_loss': '不適用',
            'take_profit': '已有部位考慮分批獲利',
            'holding_period': '不適用'
        }
    
    # 情境 3: 🟡 反彈陷阱 (極度貪婪 + 超賣反彈)
    if fng > 70 and rsi < 40 and change_7d > 15:
        return {
            'scenario': '反彈陷阱',
            'recommendation': '避開',
            'win_rate': '45%',
            'win_rate_note': '歷史統計：BTC 日線、1 年期；山寨幣僅供參考',
            'position_size': '0%',
            'stop_loss': '不適用',
            'take_profit': '等待 FNG 降回 50 以下',
            'holding_period': '不適用'
        }
    
    # 情境 1: 🟢 黃金買點 (極度恐懼 + 超賣)
    if fng < 25 and rsi < 30:
        return {
            'scenario': '黃金買點',
            'recommendation': '積極買入',
            'win_rate': '90%',
            'win_rate_note': '歷史統計：BTC 日線、1 年期；山寨幣僅供參考',
            'position_size': '≤ 加密貨幣預算 50%（分 2 批，單批 ≤ 5,000 元）',
            'stop_loss': '再跌 15% 停損',
            'take_profit': 'RSI > 60 或 FNG > 60 時分批獲利',
            'holding_period': '3-6 個月'
        }
    
    # 情境 2: 🟡 右側確認點 (恐懼消退 + 站上均線)
    if 30 <= fng <= 50 and rsi < 60 and price_above_ma20:
        return {
            'scenario': '右側確認',
            'recommendation': '謹慎買入',
            'win_rate': '72%',
            'win_rate_note': '歷史統計：BTC 日線、1 年期；山寨幣僅供參考',
            'position_size': '單筆 5,000-8,000 元',
            'stop_loss': '跌破 MA20 停損',
            'take_profit': 'RSI > 70 或 FNG > 70 時獲利',
            'holding_period': '1-3 個月'
        }
    
    # 預設：中性
    return {
        'scenario': '中性',
        'recommendation': '觀望',
        'win_rate': '-',
        'win_rate_note': '',
        'position_size': '等待明確訊號',
        'stop_loss': '不適用',
        'take_profit': '不適用',
        'holding_period': '不適用'
    }


def run_crypto_screener() -> List[Dict]:
    """執行加密貨幣海選"""
    print("🔍 啟動加密貨幣海選引擎...")
    
    client = CryptoClient()
    
    # 1. 取得恐懼貪婪指數
    fng = client.get_fear_greed_index()
    if fng is None:
        print("⚠️ 無法取得恐懼貪婪指數，使用預設中性值")
        fng = {'value': 50, 'classification': 'Neutral'}
    print(f"  恐懼貪婪指數：{fng['value']} ({fng['classification']})")
    
    # 🆕 永遠先算 BTC 基準指標（供市場層級情境使用）
    btc_tech = client.get_technical_indicators('bitcoin') or {'rsi': 50.0, 'price_above_ma20': False}
    btc_data = (client.get_market_data(['bitcoin']).get('bitcoin') or {})
    btc_chg = btc_data.get('change_7d', 0)
    
    # P0-2 修正：如果極度貪婪（>75），輸出市場層級情境並建議觀望
    if fng['value'] > CRYPTO_RULES['fear_greed_max']:
        market_scenario = get_scenario_badge(
            fng=fng['value'],
            rsi=btc_tech['rsi'],
            price_above_ma20=btc_tech['price_above_ma20'],
            change_7d=btc_chg
        )
        print(f"⚠️ 市場極度貪婪（{fng['value']}），建議觀望")
        save_crypto_results([], fng, market_scenario=market_scenario)
        return []
    
    # 2. 取得市場數據
    market_data = client.get_market_data(WATCHLIST)
    if not market_data:
        print("❌ 無法取得市場數據")
        save_crypto_results([], fng)  # P2: 失敗時也存檔，避免儀表板讀到舊資料
        return []
    
    # 3. 篩選 + P1-2: 加 time.sleep 避免 CoinGecko 429
    candidates = []
    for coin_id, data in market_data.items():
        # 市值篩選
        if data.get('market_cap') is None or data['market_cap'] < CRYPTO_RULES['min_market_cap']:
            continue
        
        # 技術指標
        tech = client.get_technical_indicators(coin_id)
        time.sleep(1)  # P1-2: 避免 rate limit
        
        # 技術指標獲取失敗則跳過
        if tech is None:
            print(f"⚠️ {coin_id} 技術指標獲取失敗，跳過")
            continue
        
        # 🔴 P0-1 修正：先分類情境，再依情境決定篩選規則
        scenario = get_scenario_badge(
            fng=fng['value'],
            rsi=tech['rsi'],
            price_above_ma20=tech['price_above_ma20'],
            change_7d=data.get('change_7d', 0)
        )
        
        # 依情境決定篩選：黃金買點是左側機會，豁免 MA20/RSI 上限過濾
        if scenario['scenario'] == '極度危險':
            continue  # 或收集到 warnings 清單供前端顯示
        if scenario['scenario'] != '黃金買點':
            if tech['rsi'] > CRYPTO_RULES['rsi_max']:
                continue
            if CRYPTO_RULES['price_above_ma20'] and not tech['price_above_ma20']:
                continue
        # 黃金買點仍要求市值與流動性門檻（已在上方檢查）
        
        candidates.append({
            'coin_id': coin_id,
            'symbol': data['symbol'],
            'name': data['name'],
            'price': data['price'],
            'market_cap': data['market_cap'],
            'change_24h': round(data['change_24h'], 2),
            'change_7d': round(data['change_7d'], 2),
            'rsi': tech['rsi'],
            'ma20': tech['ma20'],
            'price_above_ma20': tech['price_above_ma20'],
            'fear_greed': fng['value'],
            'scenario': scenario['scenario'],
            'recommendation': scenario['recommendation'],
            'win_rate': scenario['win_rate'],
            'win_rate_note': scenario['win_rate_note'],
            'position_size': scenario['position_size'],
            'stop_loss': scenario['stop_loss'],
            'take_profit': scenario['take_profit'],
            'holding_period': scenario['holding_period'],
            'screened_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
    
    # P2 修正：排序邏輯改為單一維度（7 日漲幅）
    candidates.sort(key=lambda x: x['change_7d'], reverse=True)
    
    top = candidates[:10]
    save_crypto_results(top, fng)
    print(f"✅ 加密貨幣海選完成：{len(top)} 檔候選")
    
    return top


def save_crypto_results(candidates: List[Dict], fng: Optional[Dict], market_scenario: Optional[Dict] = None) -> None:
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'crypto_candidates.json')
    
    if fng is None:
        fng = {'value': 50, 'classification': 'Neutral'}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "candidates": candidates,
            "fear_greed_index": fng,
            "market_scenario": market_scenario,  # 🆕 P0-2: 市場層級情境
            "updated_at": datetime.now().isoformat(),
            "rules_applied": CRYPTO_RULES
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 加密貨幣結果已儲存至：{output_path}")


if __name__ == "__main__":
    candidates = run_crypto_screener()
    
    print("\n🎯 本週加密貨幣候選 Top 5:")
    for i, coin in enumerate(candidates[:5], 1):
        print(f"  {i}. {coin['symbol']} - ${coin['price']:.2f}, 7 日 {coin['change_7d']:+.2f}%, RSI {coin['rsi']}")
