"""
加密貨幣數據客戶端
使用免費 API：CoinGecko + Alternative.me Fear & Greed Index
"""

import logging
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger("CryptoClient")


class CryptoClient:
    """加密貨幣 API 客戶端（完全免費，無需 API Key）"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SniperSystem/1.0"})

        # 設定自動重試機制（應對暫時性網路抖動與 429 頻率限制）
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """關閉 Session 連線"""
        self.session.close()

    def get_market_data(
        self, coin_ids: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """取得加密貨幣市場數據（價格、市值、24h/7d 漲跌幅）"""
        if coin_ids is None:
            coin_ids = ["bitcoin", "ethereum", "solana"]

        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(coin_ids),
            "price_change_percentage": "24h,7d",
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            result = {}
            for coin in data:
                cid = coin.get("id")
                if not cid:
                    continue
                result[cid] = {
                    "symbol": coin.get("symbol", "").upper(),
                    "name": coin.get("name", ""),
                    "price": coin.get("current_price"),
                    "market_cap": coin.get("market_cap"),
                    "change_24h": coin.get("price_change_percentage_24h", 0.0),
                    "change_7d": coin.get(
                        "price_change_percentage_7d_in_currency", 0.0
                    ),
                    "volume_24h": coin.get("total_volume"),
                }
            return result
        except Exception as e:
            logger.error("CoinGecko 取得市場數據失敗：%s", e)
            return {}

    def get_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """取得加密貨幣恐懼貪婪指數

        Returns:
            成功回傳 dict；失敗時回傳 None，避免回傳假中性數據干擾策略。
        """
        url = "https://api.alternative.me/fng/"
        params = {"limit": 1}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                latest = data["data"][0]
                return {
                    "value": int(latest["value"]),
                    "classification": latest["value_classification"],
                    "timestamp": int(latest["timestamp"]),
                }
        except Exception as e:
            logger.error("Fear & Greed API 請求失敗：%s", e)

        return None

    @staticmethod
    def _calculate_rsi(prices: List[float], period: int = 14) -> float:
        """計算標準 Wilder's RSI (與多數交易所計算方式一致)"""
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # 初始第一組平均收益與損失
        gains = [d if d > 0 else 0.0 for d in deltas[:period]]
        losses = [-d if d < 0 else 0.0 for d in deltas[:period]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Wilder's 平滑更新
        for d in deltas[period:]:
            gain = d if d > 0 else 0.0
            loss = -d if d < 0 else 0.0
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        return round(100.0 - (100.0 / (1.0 + rs)), 2)

    def get_technical_indicators(
        self, coin_id: str, days: int = 120
    ) -> Optional[Dict[str, Any]]:
        """計算技術指標（MA7, MA20, RSI14）

        Args:
            coin_id: 加密貨幣 ID (CoinGecko)
            days: 歷史天數 (建議 >= 91，以確保取得 daily 日線數據)
        """
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            prices = [p[1] for p in data.get("prices", []) if p[1] is not None]
            if len(prices) < 20:
                logger.warning(
                    "%s 價格數據不足 20 根，無法計算技術指標", coin_id
                )
                return None

            ma7 = sum(prices[-7:]) / 7
            ma20 = sum(prices[-20:]) / 20
            rsi = self._calculate_rsi(prices, period=14)

            return {
                "ma7": round(ma7, 2),
                "ma20": round(ma20, 2),
                "rsi": rsi,
                "price_above_ma20": prices[-1] > ma20,
            }
        except Exception as e:
            logger.error("%s 技術指標計算失敗：%s", coin_id, e)
            return None
