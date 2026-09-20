"""
加密貨幣海選引擎
篩選條件：恐懼貪婪指數 + 技術面 + 市值
情境分類：四象限決策矩陣 (RSI + FNG)
"""
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
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


def get_scenario_badge(fng: int, rsi: int, price_above_ma20: bool, change_7d: float = 0) -> Dict:
    """
    根據四象限決策矩陣判斷當前情境
    
    Returns:
        dict: {
            'scenario': str,  # 情境名稱
            'badge_html': str,  # HTML 標籤
            'recommendation': str,  # 建議策略
            'win_rate': str,  # 歷史勝率
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
            'badge_html': '<span class="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-bold">🔴 極度危險</span>',
            'recommendation': '避開',
            'win_rate': '20%',
            'position_size': '0%',
            'stop_loss': '不適用',
            'take_profit': '已有部位考慮分批獲利',
            'holding_period': '不適用'
        }
    
    # 情境 3: 🟡 反彈陷阱 (極度貪婪 + 超賣反彈)
    if fng > 70 and rsi < 40 and change_7d > 15:
        return {
            'scenario': '反彈陷阱',
            'badge_html': '<span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-bold">⚠️ 反彈陷阱</span>',
            'recommendation': '避開',
            'win_rate': '45%',
            'position_size': '0%',
            'stop_loss': '不適用',
            'take_profit': '等待 FNG 降回 50 以下',
            'holding_period': '不適用'
        }
    
    # 情境 1: 🟢 黃金買點 (極度恐懼 + 超賣)
    if fng < 25 and rsi < 30:
        return {
            'scenario': '黃金買點',
            'badge_html': '<span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-bold">🟢 黃金買點</span>',
            'recommendation': '積極買入',
            'win_rate': '90%',
            'position_size': '單筆上限 10,000 元（可分 2 批）',
            'stop_loss': '再跌 15% 停損',
            'take_profit': 'RSI > 60 或 FNG > 60 時分批獲利',
            'holding_period': '3-6 個月'
        }
    
    # 情境 2: 🟡 右側確認點 (恐懼消退 + 站上均線)
    if 30 <= fng <= 50 and rsi < 60 and price_above_ma20:
        return {
            'scenario': '右側確認',
            'badge_html': '<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-bold">🔵 右側確認</span>',
            'recommendation': '謹慎買入',
            'win_rate': '72%',
            'position_size': '單筆 5,000-8,000 元',
            'stop_loss': '跌破 MA20 停損',
            'take_profit': 'RSI > 70 或 FNG > 70 時獲利',
            'holding_period': '1-3 個月'
        }
    
    # 預設：中性
    return {
        'scenario': '中性',
        'badge_html': '<span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">⚪ 中性</span>',
        'recommendation': '觀望',
        'win_rate': '-',
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
    
    # 如果極度貪婪（>75），建議觀望
    if fng['value'] > CRYPTO_RULES['fear_greed_max']:
        print(f"⚠️ 市場極度貪婪（{fng['value']}），建議觀望")
        save_crypto_results([], fng)
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
        
        # RSI 篩選
        if tech['rsi'] > CRYPTO_RULES['rsi_max']:
            continue
        
        # MA20 篩選
        if CRYPTO_RULES['price_above_ma20'] and not tech['price_above_ma20']:
            continue
        
        # 情境分類（四象限決策矩陣）
        scenario = get_scenario_badge(
            fng=fng['value'],
            rsi=tech['rsi'],
            price_above_ma20=tech['price_above_ma20'],
            change_7d=data.get('change_7d', 0)
        )
        
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
            'badge_html': scenario['badge_html'],
            'recommendation': scenario['recommendation'],
            'win_rate': scenario['win_rate'],
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


def save_crypto_results(candidates: List[Dict], fng: Optional[Dict]) -> None:
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'crypto_candidates.json')
    
    if fng is None:
        fng = {'value': 50, 'classification': 'Neutral'}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "candidates": candidates,
            "fear_greed_index": fng,
            "updated_at": datetime.now().isoformat(),
            "rules_applied": CRYPTO_RULES
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 加密貨幣結果已儲存至：{output_path}")


if __name__ == "__main__":
    candidates = run_crypto_screener()
    
    print("\n🎯 本週加密貨幣候選 Top 5:")
    for i, coin in enumerate(candidates[:5], 1):
        print(f"  {i}. {coin['symbol']} - ${coin['price']:.2f}, 7 日 {coin['change_7d']:+.2f}%, RSI {coin['rsi']}")
