"""
加密貨幣海選引擎
篩選條件：恐懼貪婪指數 + 技術面 + 市值
"""
import json
import os
from datetime import datetime
from typing import List, Dict
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


def run_crypto_screener() -> List[Dict]:
    """執行加密貨幣海選"""
    print("🔍 啟動加密貨幣海選引擎...")
    
    client = CryptoClient()
    
    # 1. 取得恐懼貪婪指數
    fng = client.get_fear_greed_index()
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
        if data['market_cap'] < CRYPTO_RULES['min_market_cap']:
            continue
        
        # 技術指標
        tech = client.get_technical_indicators(coin_id)
        time.sleep(1)  # P1-2: 避免 rate limit
        
        # RSI 篩選
        if tech['rsi'] > CRYPTO_RULES['rsi_max']:
            continue
        
        # MA20 篩選
        if CRYPTO_RULES['price_above_ma20'] and not tech['price_above_ma20']:
            continue
        
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
            'screened_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
    
    # P2 修正：排序邏輯改為單一維度（7 日漲幅）
    candidates.sort(key=lambda x: x['change_7d'], reverse=True)
    
    top = candidates[:10]
    save_crypto_results(top, fng)
    print(f"✅ 加密貨幣海選完成：{len(top)} 檔候選")
    
    return top


def save_crypto_results(candidates: List[Dict], fng: Dict) -> None:
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'crypto_candidates.json')
    
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
