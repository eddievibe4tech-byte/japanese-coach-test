"""
FinMind API 客戶端模組
提供台股數據抓取功能：營收、投信籌碼、融資餘額等
"""
import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FinMindClient:
    """FinMind API 客戶端"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 FinMind 客戶端
        
        Args:
            token: FinMind API Token，若未提供則從環境變數 FINMIND_TOKEN 讀取
        """
        self.token = token or os.getenv('FINMIND_TOKEN', '')
        self.base_url = 'https://api.finmindtrade.com/api/v4/data'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SniperSystem/1.0',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, dataset: str, stock_id: str, days: int = 60) -> Optional[List[Dict]]:
        """
        發送 API 請求
        
        Args:
            dataset: 數據集名稱
            stock_id: 股票代號（v4 用 data_id）
            days: 日期範圍天數
            
        Returns:
            API 回應資料（data 陣列），失敗時返回 None
        """
        if not self.token:
            raise ValueError("FinMind Token 未設定")
        
        end = datetime.now()
        start = end - timedelta(days=days)
        
        request_params = {
            'dataset': dataset,
            'data_id': stock_id,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'token': self.token,
        }
        
        try:
            response = self.session.get(self.base_url, params=request_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 200:
                # FinMind 回傳的 data 直接是陣列
                return data.get('data', [])
            else:
                logger.error(f"FinMind {dataset} 失敗：{data.get('status')} {data.get('msg', 'Unknown error')}")
                return None
                
        except requests.exceptions.Timeout:
            print("API 請求超時")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"FinMind {dataset} 請求失敗：{e}")
            return None
    
    def get_revenue(self, stock_id: str, months: int = 3) -> Optional[Dict]:
        """
        取得股票月營收資料
        
        Args:
            stock_id: 股票代號
            months: 要取得的月數
            
        Returns:
            包含最新月營收年增率的字典
        """
        data = self._make_request('TaiwanStockMonthRevenue', stock_id, days=months*30) or []
        
        if not data:
            return None
        
        # 解析營收資料 (data 直接是陣列)
        revenue_data = data
        if not revenue_data:
            return None
        
        # 取最新一筆資料
        latest = revenue_data[-1]
        
        # 計算年增率
        current_revenue = float(latest.get('revenue', 0))
        
        # 簡化：假設 API 已提供 YoY 或我們用前後月比較
        # 實際應比較去年同月，此處簡化演示
        yoy_growth = 0.0
        if len(revenue_data) >= 2:
            prev_month = revenue_data[-2]
            prev_revenue = float(prev_month.get('revenue', 0))
            if prev_revenue > 0:
                yoy_growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
        
        return {
            'date': latest.get('date', ''),
            'revenue': current_revenue,
            'yoy_growth': round(yoy_growth, 2)
        }
    
    def get_institutional_buy(self, stock_id: str, days: int = 10) -> Optional[int]:
        """
        取得投信連續買超天數
        
        Args:
            stock_id: 股票代號
            days: 檢查的天數範圍
            
        Returns:
            連續買超天數
        """
        data = self._make_request('TaiwanStockInstitutionalInvestorsBuySell', stock_id, days=days) or []
        
        if not data:
            return 0
        
        institutional_data = data
        if not institutional_data:
            return 0
        
        # 計算投信連續買超天數
        consecutive_buy_days = 0
        
        # 由最近往回推
        for record in reversed(institutional_data):
            buy = int(record.get('buy', 0))
            sell = int(record.get('sell', 0))
            net_buy = record.get('net_buy', buy - sell)
            
            if net_buy > 0:
                consecutive_buy_days += 1
            else:
                break
        
        return consecutive_buy_days
    
    def get_margin_balance(self, stock_id: str, days: int = 10) -> int:
        """
        計算融資增減 (今日餘額 - 昨日餘額)
        
        Args:
            stock_id: 股票代號
            days: 檢查的天數範圍
            
        Returns:
            融資增減張數
        """
        # ✅ 修正 Dataset 名稱
        data = self._make_request('TaiwanStockMarginPurchaseShortSale', stock_id, days=days)
        if not data or len(data) < 2:
            return 0
        
        # ✅ 修正欄位名稱 (取最近兩筆)
        latest = data[-1]
        prev = data[-2]
        
        today_balance = latest.get('MarginPurchaseTodayBalance', 0)
        yesterday_balance = prev.get('MarginPurchaseTodayBalance', 0)
        
        # 回傳增減張數 (FinMind 單位通常是張)
        return int(today_balance - yesterday_balance)
    
    def get_stock_price(self, stock_id: str, days: int = 30) -> Optional[List[float]]:
        """
        取得股票收盤價列表
        
        Args:
            stock_id: 股票代號
            days: 要取得的天數
            
        Returns:
            收盤價列表
        """
        data = self._make_request('TaiwanStockPrice', stock_id, days=days) or []
        
        if not data:
            return []
        
        price_data = data
        if not price_data:
            return []
        
        # 提取收盤價
        prices = []
        for record in price_data:
            close_price = float(record.get('close', 0))
            prices.append(close_price)
        
        return prices
