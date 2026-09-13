"""
AI 新聞情緒分析與深度盡調模組
使用免費搜尋引擎 + Groq 進行 AI 盡調，替代 Perplexity/Claude
"""
import json
import os
from typing import Dict, Optional
from groq_client import GroqClient

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    print("⚠️ 警告：未安裝 duckduckgo-search，請執行：pip install duckduckgo-search")


def search_news(stock_code: str, stock_name: str, max_results: int = 5) -> list:
    """
    使用 DuckDuckGo 搜尋近期新聞
    
    Args:
        stock_code: 股票代號
        stock_name: 股票名稱
        max_results: 最大結果數
        
    Returns:
        新聞標題列表
    """
    if not DUCKDUCKGO_AVAILABLE:
        # 若無 DuckDuckGo，回傳空清單（不中斷流程）
        print("⚠️ DuckDuckGo 不可用，跳過新聞搜尋")
        return []
    
    query = f"{stock_name} {stock_code} 財報 營收 法說會 利多 利空"
    news_titles = []
    
    try:
        with DDGS(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as ddgs:
            results = ddgs.news(query, region="tw-tw", max_results=max_results)
            news_titles = [r['title'] for r in results]
            
        print(f"📰 找到 {len(news_titles)} 則新聞")
        
    except Exception as e:
        print(f"⚠️ 新聞搜尋失敗：{e}")
    
    return news_titles


def ai_due_diligence(stock_code: str, stock_name: str, news_titles: list = None) -> Dict:
    """
    使用 Groq 進行 AI 深度盡調（華爾街分析師視角）
    
    Args:
        stock_code: 股票代號
        stock_name: 股票名稱
        news_titles: 新聞標題列表（若為 None 則自動搜尋）
        
    Returns:
        包含情緒、風險、結論的字典
    """
    # 1. 若未提供新聞，自動搜尋
    if news_titles is None:
        news_titles = search_news(stock_code, stock_name)
    
    # 2. 若無新聞，回傳中性結果
    if not news_titles:
        return {
            "sentiment": "Neutral",
            "risk_factor": "無近期重大新聞",
            "conclusion": f"{stock_name} 近期無重大消息，建議參考技術面與籌碼面"
        }
    
    # 3. 呼叫 Groq 進行深度分析 (使用既有的 call_groq_api 函數)
    groq = GroqClient()
    
    prompt = f"""你是一位嚴格的華爾街分析師。請根據以下關於 {stock_name}({stock_code}) 的近期新聞標題，進行盡職調查 (Due Diligence)。

【新聞標題】
{json.dumps(news_titles, ensure_ascii=False)}

【任務】
1. 判斷整體市場情緒 (Bullish / Neutral / Bearish)
2. 找出管理層或市場可能「隱瞞」或「擔憂」的最大風險 (Risk Factor)
3. 給出 50 字以內的投資結論

請僅輸出 JSON：
{{
  "sentiment": "Bullish/Neutral/Bearish",
  "risk_factor": "主要風險描述",
  "conclusion": "投資結論"
}}"""

    # 🔴 P0 修正：使用 GroqClient._make_request 方法（既有介面）
    response = groq._make_request(
        messages=[
            {"role": "system", "content": "你是一位嚴格的華爾街分析師，專精於財報與新聞分析。請僅輸出 JSON 格式。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    if not response:
        return {
            "sentiment": "Error",
            "risk_factor": "AI 解析失敗",
            "conclusion": "N/A"
        }
    
    try:
        # 🔴 P0 修正：response 已經是完整的 API 回應，需要解析 choices
        content = response['choices'][0]['message']['content']
        # 清理 Markdown 標記
        clean = content.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean)
        
        return {
            "sentiment": result.get("sentiment", "Neutral"),
            "risk_factor": result.get("risk_factor", "未知風險"),
            "conclusion": result.get("conclusion", "無結論")
        }
        
    except Exception as e:
        print(f"⚠️ AI 解析失敗：{e}")
        return {
            "sentiment": "Error",
            "risk_factor": "AI 解析失敗",
            "conclusion": "N/A"
        }


def run_ai_dd_on_candidates(candidates_file: str = None) -> list:
    """
    對海選出的候選股執行 AI 盡調
    
    Args:
        candidates_file: 候選股 JSON 檔案路徑（預設為 data/screener_candidates.json）
        
    Returns:
        AI 盡調報告列表
    """
    if candidates_file is None:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        candidates_file = os.path.join(data_dir, 'screener_candidates.json')
    
    # 讀取候選股
    if not os.path.exists(candidates_file):
        print(f"❌ 候選股檔案不存在：{candidates_file}")
        return []
    
    with open(candidates_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('candidates', [])
    
    if not candidates:
        print("⚠️ 無候選股需要分析")
        return []
    
    print(f"🤖 開始對 {len(candidates)} 檔候選股執行 AI 盡調...")
    
    reports = []
    for i, stock in enumerate(candidates, 1):
        print(f"\n[{i}/{len(candidates)}] 分析 {stock['code']} {stock['name']}...")
        
        report = ai_due_diligence(
            stock_code=stock['code'],
            stock_name=stock['name']
        )
        
        report['code'] = stock['code']
        report['name'] = stock['name']
        report['analyzed_at'] = __import__('datetime').datetime.now().isoformat()
        
        reports.append(report)
        
        # 顯示摘要
        print(f"  情緒：{report['sentiment']}, 風險：{report['risk_factor'][:30]}...")
    
    # 儲存結果
    save_ai_dd_reports(reports)
    
    return reports


def save_ai_dd_reports(reports: list) -> None:
    """
    儲存 AI 盡調報告到 JSON 檔案
    
    Args:
        reports: 報告列表
    """
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, 'ai_dd_reports.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "reports": reports,
            "updated_at": __import__('datetime').datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 AI 盡調報告已儲存至：{output_path}")


if __name__ == "__main__":
    # 測試執行
    print("🧪 測試 AI 盡調功能...")
    
    # 測試單一股票
    test_stock = {"code": "2330", "name": "台積電"}
    report = ai_due_diligence(
        stock_code=test_stock["code"],
        stock_name=test_stock["name"]
    )
    
    print(f"\n✅ {test_stock['name']} 盡調結果:")
    print(f"  情緒：{report['sentiment']}")
    print(f"  風險：{report['risk_factor']}")
    print(f"  結論：{report['conclusion']}")
