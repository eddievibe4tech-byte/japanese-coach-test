"""
風險計算器模組
提供波動率計算、風險等級評估、產業集中度檢查等功能
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime


def calculate_volatility(prices: List[float], period: int = 20) -> float:
    """
    計算指定週期的波動率（標準差 / 均值 * 100）
    
    Args:
        prices: 收盤價列表
        period: 計算週期，預設 20 日
        
    Returns:
        波動率百分比
    """
    if len(prices) < 2:
        return 0.0
    
    # 取最近 period 天的價格
    recent_prices = prices[-period:] if len(prices) >= period else prices
    
    if len(recent_prices) < 2:
        return 0.0
    
    # 計算每日報酬率
    returns = []
    for i in range(1, len(recent_prices)):
        if recent_prices[i-1] != 0:
            daily_return = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            returns.append(daily_return)
    
    if len(returns) < 2:
        return 0.0
    
    # 計算標準差
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    # 年化波動率並轉換為百分比
    annualized_volatility = std_dev * (252 ** 0.5) * 100
    
    return round(annualized_volatility, 2)


def assess_risk_level(volatility: float, volatility_limit: float = 30.0) -> str:
    """
    根據波動率評估風險等級
    
    Args:
        volatility: 波動率百分比
        volatility_limit: 波動率警戒線
        
    Returns:
        風險等級字串 (🟢 低風險 / 🟡 中風險 / 🟠 高風險 / 🔴 極高風險)
    """
    if volatility < volatility_limit * 0.5:
        return "🟢 低風險"
    elif volatility < volatility_limit:
        return "🟡 中風險"
    elif volatility < volatility_limit * 1.5:
        return "🟠 高風險"
    else:
        return "🔴 極高風險"


def check_industry_concentration(
    stocks: List[Dict],
    industry_limit_percent: float = 40.0
) -> Tuple[bool, Dict[str, float], List[str]]:
    """
    檢查投資組合的產業集中度
    
    Args:
        stocks: 股票清單，每個元素包含 'industry' 鍵
        industry_limit_percent: 產業集中度上限
        
    Returns:
        (是否超標, 產業分佈字典, 警告訊息列表)
    """
    if not stocks:
        return False, {}, []
    
    # 計算各產業佔比
    industry_count: Dict[str, int] = {}
    for stock in stocks:
        industry = stock.get('industry', '未知')
        industry_count[industry] = industry_count.get(industry, 0) + 1
    
    total_stocks = len(stocks)
    industry_distribution: Dict[str, float] = {}
    warnings: List[str] = []
    is_exceeded = False
    
    for industry, count in industry_count.items():
        percentage = (count / total_stocks) * 100
        industry_distribution[industry] = round(percentage, 2)
        
        if percentage > industry_limit_percent:
            is_exceeded = True
            warnings.append(f"{industry}產業佔比{percentage:.1f}%超過上限{industry_limit_percent}%")
    
    return is_exceeded, industry_distribution, warnings


def calculate_risk_score(
    volatility: float,
    industry_exceeded: bool,
    high_risk_count: int,
    total_positions: int,
    volatility_limit: float = 30.0
) -> int:
    """
    計算整體風險分數 (0-100)
    
    Args:
        volatility: 平均波動率
        industry_exceeded: 產業集中度是否超標
        high_risk_count: 高風險標的數量
        total_positions: 總持倉數量
        volatility_limit: 波動率警戒線
        
    Returns:
        風險分數 (0-100)
    """
    score = 0
    
    # 波動率分數 (最高 40 分)
    if volatility > volatility_limit * 1.5:
        score += 40
    elif volatility > volatility_limit:
        score += 25
    elif volatility > volatility_limit * 0.5:
        score += 10
    
    # 產業集中度分數 (最高 30 分)
    if industry_exceeded:
        score += 30
    
    # 高風險標的比例分數 (最高 30 分)
    if total_positions > 0:
        high_risk_ratio = high_risk_count / total_positions
        if high_risk_ratio > 0.5:
            score += 30
        elif high_risk_ratio > 0.3:
            score += 20
        elif high_risk_ratio > 0.1:
            score += 10
    
    return min(score, 100)


def get_risk_status(risk_score: int) -> str:
    """
    根據風險分數取得風險狀態
    
    Args:
        risk_score: 風險分數 (0-100)
        
    Returns:
        風險狀態字串 (✅ 安全 / 🟡 注意 / 🔴 危險)
    """
    if risk_score <= 30:
        return "✅ 安全"
    elif risk_score <= 60:
        return "🟡 注意"
    else:
        return "🔴 危險"


def get_risk_suggestion(risk_score: int, risk_status: str) -> str:
    """
    根據風險狀態提供建議動作
    
    Args:
        risk_score: 風險分數
        risk_status: 風險狀態
        
    Returns:
        建議動作字串
    """
    if risk_status == "✅ 安全":
        return "可正常操作"
    elif risk_status == "🟡 注意":
        return "建議減碼或觀察"
    else:
        return "建議減碼或觀望"
