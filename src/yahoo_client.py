"""
Yahoo Finance 備援客戶端模組
當 FinMind API 限流或失敗時，使用 Yahoo Finance 抓取股價與技術指標
"""
import yfinance as yf
import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """
    備援客戶端：當 FinMind 限流時，使用 Yahoo Finance 抓取股價與技術指標
    
    特性：
    - 台股代碼需加上 .TW (例如 2330.TW)
    - 無嚴格 API Key 限制，不會有 429 Rate Limit 問題
    - 可計算所有技術指標 (MA, RSI, MACD, 波動率)
    - 缺點：無法取得三大法人買賣和融資融券數據
    """
    
    def get_stock_data(self, code: str, period: str = "3mo") -> Optional[Dict]:
        """
        取得股價歷史數據並計算技術指標
        
        Args:
            code: 股票代號 (台股不需加 .TW，此處會自動處理)
            period: 歷史數據期間 ("1mo", "3mo", "6mo", "1y", etc.)
            
        Returns:
            包含股價數據和技術指標的字典，失敗時返回 None
        """
        try:
            # 台股代碼需加上 .TW
            ticker = yf.Ticker(f"{code}.TW")
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"Yahoo Finance: {code} 無歷史數據")
                return None
            
            # 計算收盤價列表 (供 main.py 使用)
            prices = hist['Close'].tolist()
            
            # 計算技術指標
            last_price = prices[-1]
            ma5 = hist['Close'].rolling(window=5).mean().iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            
            # 計算 RSI (14)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 計算 MACD
            ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
            ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = (ema12 - ema26).iloc[-1]
            
            # 計算波動率 (年化)
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5) * 100
            
            # 計算 5 日漲跌幅
            if len(prices) >= 6:
                change_5d = ((prices[-1] / prices[-6]) - 1) * 100
            else:
                change_5d = 0.0
                
            return {
                'prices': prices,
                'current_price': last_price,
                'ma5': float(ma5),
                'ma20': float(ma20),
                'rsi': float(rsi),
                'macd': float(macd),
                'volatility': float(volatility),
                'change_5d': float(change_5d),
                'price_above_ma20': bool(last_price > ma20),
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance 抓取 {code} 失敗：{e}")
            return None

    def get_basic_info(self, code: str) -> Optional[Dict]:
        """
        取得基本財報資訊 (EPS, 本益比等)
        
        Args:
            code: 股票代號
            
        Returns:
            包含基本財報資訊的字典，失敗時返回 None
        """
        try:
            ticker = yf.Ticker(f"{code}.TW")
            info = ticker.info
            return {
                'eps': info.get('trailingEps', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'market_cap': info.get('marketCap', 0),
            }
        except Exception as e:
            logger.warning(f"Yahoo Finance 財報資訊抓取失敗：{e}")
            return None
