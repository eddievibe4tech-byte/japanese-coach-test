"""
FinMind 客戶端單元測試
使用 responses 庫 Mock HTTP 請求
"""
import pytest
import responses
from src.finmind_client import FinMindClient


class TestFinMindClientInit:
    """測試 FinMindClient 初始化"""
    
    def test_init_with_token(self):
        """測試提供 Token 的初始化"""
        client = FinMindClient(token='test_token')
        assert client.token == 'test_token'
    
    def test_init_without_token(self, monkeypatch):
        """測試未提供 Token 時的初始化"""
        monkeypatch.delenv('FINMIND_TOKEN', raising=False)
        client = FinMindClient()
        assert client.token == ''
    
    def test_init_from_env(self, monkeypatch):
        """測試從環境變數讀取 Token"""
        monkeypatch.setenv('FINMIND_TOKEN', 'env_token')
        client = FinMindClient()
        assert client.token == 'env_token'


class TestMakeRequest:
    """測試 API 請求"""
    
    @responses.activate
    def test_successful_request(self):
        """測試成功的 API 請求"""
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json={'status': 200, 'msg': 'success', 'data': [{'date': '2024-01-01', 'revenue': 100}]},
            status=200
        )
        
        client = FinMindClient(token='test_token')
        # ✅ 實際呼叫公開方法間接測試 _make_request
        result = client.get_revenue('2330', months=1)
        assert result is not None
        assert result['revenue'] == 100.0
    
    @responses.activate
    def test_api_error(self):
        """測試 API 錯誤回應"""
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json={'status': 400, 'msg': 'Invalid token'},
            status=200
        )
        
        # ✅ 實際呼叫方法來觸發處理邏輯
        client = FinMindClient(token='test_token')
        result = client.get_revenue('2330', months=1)
        # API 失敗時應返回 None
        assert result is None


class TestGetRevenue:
    """測試營收數據抓取"""
    
    @responses.activate
    def test_get_revenue_success(self):
        """測試成功取得營收數據"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                {'date': '2024-01-01', 'revenue': 1000000},
                {'date': '2024-02-01', 'revenue': 1200000}
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        result = client.get_revenue('2330')
        
        assert result is not None
        assert 'revenue' in result
        assert 'yoy_growth' in result
    
    @responses.activate
    def test_get_revenue_empty_data(self):
        """測試空營收數據"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': []
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        result = client.get_revenue('2330')
        
        assert result is None
    
    @responses.activate
    def test_get_revenue_api_failure(self):
        """測試 API 失敗"""
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json={'status': 500, 'msg': 'Server error'},
            status=200
        )
        
        client = FinMindClient(token='test_token')
        result = client.get_revenue('2330')
        
        assert result is None
    
    def test_get_revenue_no_token(self):
        """測試未設定 Token"""
        client = FinMindClient(token='')
        
        with pytest.raises(ValueError, match="FinMind Token 未設定"):
            client.get_revenue('2330')


class TestGetInstitutionalBuy:
    """測試投信買超數據"""
    
    @responses.activate
    def test_consecutive_buy_days(self):
        """測試連續買超天數計算"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                {'date': '2024-01-01', 'buy': 100, 'sell': 50},
                {'date': '2024-01-02', 'buy': 200, 'sell': 100},
                {'date': '2024-01-03', 'buy': 150, 'sell': 80},
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        days = client.get_institutional_buy('2330')
        
        assert days == 3  # 三天都淨買超
    
    @responses.activate
    def test_broken_streak(self):
        """測試買超中斷"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                {'date': '2024-01-01', 'buy': 100, 'sell': 50},
                {'date': '2024-01-02', 'buy': 50, 'sell': 100},  # 賣超
                {'date': '2024-01-03', 'buy': 200, 'sell': 100},
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        days = client.get_institutional_buy('2330')
        
        assert days == 1  # 只有最後一天買超


class TestGetMarginBalance:
    """測試融資餘額數據"""
    
    @responses.activate
    def test_margin_increase(self):
        """測試融資增加"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                # ✅ 修正：使用 FinMind API v4 實際的欄位名稱
                {'date': '2024-01-01', 'MarginPurchaseTodayBalance': 1000},
                {'date': '2024-01-05', 'MarginPurchaseTodayBalance': 1500}
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        change = client.get_margin_balance('2330')
        
        assert change == 500
    
    @responses.activate
    def test_margin_decrease(self):
        """測試融資減少"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                # ✅ 修正：使用 FinMind API v4 實際的欄位名稱
                {'date': '2024-01-01', 'MarginPurchaseTodayBalance': 1500},
                {'date': '2024-01-05', 'MarginPurchaseTodayBalance': 1000}
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        change = client.get_margin_balance('2330')
        
        assert change == -500


class TestGetStockPrice:
    """測試股價數據"""
    
    @responses.activate
    def test_get_prices_success(self):
        """測試成功取得股價"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': [
                {'date': '2024-01-01', 'close': 100},
                {'date': '2024-01-02', 'close': 102},
                {'date': '2024-01-03', 'close': 101}
            ]
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        prices = client.get_stock_price('2330')
        
        assert len(prices) == 3
        assert prices == [100.0, 102.0, 101.0]
    
    @responses.activate
    def test_get_prices_empty(self):
        """測試空股價數據"""
        mock_data = {
            'status': 200,
            'msg': 'success',
            'data': []
        }
        
        responses.add(
            responses.GET,
            'https://api.finmindtrade.com/api/v4/data',
            json=mock_data,
            status=200
        )
        
        client = FinMindClient(token='test_token')
        prices = client.get_stock_price('2330')
        
        assert prices == []
