"""
風險計算器單元測試
使用 TDD 方式編寫，涵蓋波動率、風險等級、產業集中度等測試
"""
import pytest
from src.risk_calculator import (
    calculate_volatility,
    assess_risk_level,
    check_industry_concentration,
    calculate_risk_score,
    get_risk_status,
    get_risk_suggestion
)


class TestCalculateVolatility:
    """測試波動率計算"""
    
    def test_normal_volatility(self):
        """測試正常情況下的波動率計算"""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                  110, 112, 111, 113, 115, 114, 116, 118, 117, 119]
        volatility = calculate_volatility(prices, period=20)
        
        assert volatility > 0
        assert isinstance(volatility, float)
    
    def test_insufficient_data(self):
        """測試數據不足時的處理"""
        prices = [100]
        volatility = calculate_volatility(prices)
        assert volatility == 0.0
    
    def test_empty_prices(self):
        """測試空價格列表"""
        prices = []
        volatility = calculate_volatility(prices)
        assert volatility == 0.0
    
    def test_low_volatility(self):
        """測試低波動率情境"""
        # 幾乎不變的價格
        prices = [100, 100.1, 100, 100.2, 100.1, 100, 100.1, 100.2, 100.1, 100]
        volatility = calculate_volatility(prices)
        assert volatility < 10  # 應該很低
    
    def test_high_volatility(self):
        """測試高波動率情境"""
        # 劇烈波動的價格
        prices = [100, 120, 90, 130, 80, 140, 70, 150, 60, 160]
        volatility = calculate_volatility(prices)
        assert volatility > 50  # 應該很高


class TestAssessRiskLevel:
    """測試風險等級評估"""
    
    def test_low_risk(self):
        """測試低風險等級"""
        result = assess_risk_level(volatility=10.0, volatility_limit=30.0)
        assert result == "🟢 低風險"
    
    def test_medium_risk(self):
        """測試中風險等級"""
        result = assess_risk_level(volatility=20.0, volatility_limit=30.0)
        assert result == "🟡 中風險"
    
    def test_high_risk(self):
        """測試高風險等級"""
        result = assess_risk_level(volatility=40.0, volatility_limit=30.0)
        assert result == "🟠 高風險"
    
    def test_extreme_risk(self):
        """測試極高風險等級"""
        result = assess_risk_level(volatility=50.0, volatility_limit=30.0)
        assert result == "🔴 極高風險"
    
    def test_boundary_15_percent(self):
        """測試邊界值：15% (30% * 0.5)"""
        result = assess_risk_level(volatility=14.9, volatility_limit=30.0)
        assert result == "🟢 低風險"
        
        result = assess_risk_level(volatility=15.1, volatility_limit=30.0)
        assert result == "🟡 中風險"
    
    def test_boundary_30_percent(self):
        """測試邊界值：30%"""
        result = assess_risk_level(volatility=29.9, volatility_limit=30.0)
        assert result == "🟡 中風險"
        
        result = assess_risk_level(volatility=30.1, volatility_limit=30.0)
        assert result == "🟠 高風險"
    
    def test_boundary_45_percent(self):
        """測試邊界值：45% (30% * 1.5)"""
        result = assess_risk_level(volatility=44.9, volatility_limit=30.0)
        assert result == "🟠 高風險"
        
        result = assess_risk_level(volatility=45.1, volatility_limit=30.0)
        assert result == "🔴 極高風險"


class TestCheckIndustryConcentration:
    """測試產業集中度檢查"""
    
    def test_no_exceed(self):
        """測試未超過上限"""
        stocks = [
            {'industry': '半導體'},
            {'industry': '電子'},
            {'industry': '金融'},
            {'industry': '塑化'}
        ]
        is_exceeded, distribution, warnings = check_industry_concentration(stocks, 40.0)
        
        assert is_exceeded is False
        assert len(warnings) == 0
        assert len(distribution) == 4
    
    def test_exceed_limit(self):
        """測試超過上限"""
        stocks = [
            {'industry': '半導體'},
            {'industry': '半導體'},
            {'industry': '半導體'},
            {'industry': '電子'}
        ]
        is_exceeded, distribution, warnings = check_industry_concentration(stocks, 40.0)
        
        assert is_exceeded is True
        assert len(warnings) == 1
        assert '半導體' in warnings[0]
    
    def test_empty_stocks(self):
        """測試空股票清單"""
        stocks = []
        is_exceeded, distribution, warnings = check_industry_concentration(stocks, 40.0)
        
        assert is_exceeded is False
        assert distribution == {}
        assert warnings == []
    
    def test_single_industry(self):
        """測試單一產業"""
        stocks = [
            {'industry': '半導體'},
            {'industry': '半導體'}
        ]
        is_exceeded, distribution, warnings = check_industry_concentration(stocks, 40.0)
        
        assert is_exceeded is True
        assert distribution['半導體'] == 100.0


class TestCalculateRiskScore:
    """測試風險分數計算"""
    
    def test_low_risk_score(self):
        """測試低風險分數"""
        score = calculate_risk_score(
            volatility=10.0,
            industry_exceeded=False,
            high_risk_count=0,
            total_positions=3,
            volatility_limit=30.0
        )
        assert score <= 30
    
    def test_high_risk_score(self):
        """測試高風險分數"""
        score = calculate_risk_score(
            volatility=50.0,
            industry_exceeded=True,
            high_risk_count=3,
            total_positions=3,
            volatility_limit=30.0
        )
        assert score >= 80
    
    def test_max_score_cap(self):
        """測試分數上限為 100"""
        score = calculate_risk_score(
            volatility=100.0,
            industry_exceeded=True,
            high_risk_count=10,
            total_positions=10,
            volatility_limit=30.0
        )
        assert score <= 100
    
    def test_zero_positions(self):
        """測試零持倉情況"""
        score = calculate_risk_score(
            volatility=20.0,
            industry_exceeded=False,
            high_risk_count=0,
            total_positions=0,
            volatility_limit=30.0
        )
        assert score >= 0


class TestGetRiskStatus:
    """測試風險狀態取得"""
    
    def test_safe_status(self):
        """測試安全狀態"""
        status = get_risk_status(20)
        assert status == "✅ 安全"
    
    def test_warning_status(self):
        """測試注意狀態"""
        status = get_risk_status(45)
        assert status == "🟡 注意"
    
    def test_danger_status(self):
        """測試危險狀態"""
        status = get_risk_status(75)
        assert status == "🔴 危險"
    
    def test_boundary_30(self):
        """測試邊界值 30"""
        status = get_risk_status(30)
        assert status == "✅ 安全"
        
        status = get_risk_status(31)
        assert status == "🟡 注意"
    
    def test_boundary_60(self):
        """測試邊界值 60"""
        status = get_risk_status(60)
        assert status == "🟡 注意"
        
        status = get_risk_status(61)
        assert status == "🔴 危險"


class TestGetRiskSuggestion:
    """測試風險建議取得"""
    
    def test_safe_suggestion(self):
        """測試安全狀態的建議"""
        suggestion = get_risk_suggestion(20, "✅ 安全")
        assert suggestion == "可正常操作"
    
    def test_warning_suggestion(self):
        """測試注意狀態的建議"""
        suggestion = get_risk_suggestion(45, "🟡 注意")
        assert suggestion == "建議減碼或觀察"
    
    def test_danger_suggestion(self):
        """測試危險狀態的建議"""
        suggestion = get_risk_suggestion(75, "🔴 危險")
        assert suggestion == "建議減碼或觀望"
