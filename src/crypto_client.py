"""
加密貨幣數據客戶端
使用免費 API：CoinGecko + Alternative.me Fear & Greed Index
"""
import requests
import time
from typing import Dict, List
from datetime import datetime


class CryptoClient:
    """加密貨幣 API 客戶端（完全免費，無需 API Key）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SniperSystem/1.0'})
    
    def get_market_data(self, coin_ids: List[str] = None) -> Dict:
        """
        取得加密貨幣市場數據（價格、市值、24h 漲跌幅）
        
        Args:
            coin_ids: 加密貨幣 ID 列表（CoinGecko 格式）
            
        Returns:
            {coin_id: {price, market_cap, change_24h, ...}}
        """
        if coin_ids is None:
            coin_ids = ['bitcoin', 'ethereum', 'solana']
        
        ids_str = ','.join(coin_ids)
        # P1-2 修正：明確要求 24h 和 7d 漲跌幅
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&price_change_percentage=24h,7d"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for coin in data:
                result[coin['id']] = {
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'market_cap': coin['market_cap'],
                    'change_24h': coin.get('price_change_percentage_24h', 0),
                    'change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                    'volume_24h': coin['total_volume'],
                }
            return result
        except Exception as e:
            print(f"⚠️ CoinGecko API 失敗：{e}")
            return {}
    
    def get_fear_greed_index(self) -> Dict:
        """
        取得加密貨幣恐懼貪婪指數（Alternative.me 免費 API）
        
        Returns:
            {value: 0-100, classification: "Extreme Fear"/"Fear"/"Neutral"/"Greed"/"Extreme Greed"}
        """
        url = "https://api.alternative.me/fng/?limit=1"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data'):
                latest = data['data'][0]
                return {
                    'value': int(latest['value']),
                    'classification': latest['value_classification'],
                    'timestamp': latest['timestamp']
                }
        except Exception as e:
            print(f"⚠️ Fear & Greed API 失敗：{e}")
        
        return {'value': 50, 'classification': 'Neutral'}
    
    def get_technical_indicators(self, coin_id: str, days: int = 120) -> Dict:
        """
        計算技術指標（MA、RSI）— 使用 CoinGecko 歷史價格
        
        P1-2 修正：days >= 91 才會回傳日線數據（<91 為小時線）
        
        Args:
            coin_id: 加密貨幣 ID
            days: 歷史天數（建議 >= 91 以取得日線）
            
        Returns:
            {ma7, ma20, rsi, price_above_ma20}
        """
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            prices = [p[1] for p in data.get('prices', [])]
            if len(prices) < 20:
                return {'ma7': 0, 'ma20': 0, 'rsi': 50, 'price_above_ma20': False}
            
            ma7 = sum(prices[-7:]) / 7
            ma20 = sum(prices[-20:]) / 20
            
            # 簡化 RSI 計算
            changes = [prices[i] - prices[i-1] for i in range(-14, 0)]
            gains = [c for c in changes if c > 0]
            losses = [-c for c in changes if c < 0]
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0.0001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'ma7': round(ma7, 2),
                'ma20': round(ma20, 2),
                'rsi': round(rsi, 2),
                'price_above_ma20': prices[-1] > ma20
            }
        except Exception as e:
            print(f"⚠️ {coin_id} 技術指標計算失敗：{e}")
            return {'ma7': 0, 'ma20': 0, 'rsi': 50, 'price_above_ma20': False}
