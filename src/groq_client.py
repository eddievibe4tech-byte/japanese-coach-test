"""
Groq API 客戶端模組
提供 AI 分析功能：股票評分、市場體制判斷等
"""
import os
import json
import time
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq API 客戶端"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        初始化 Groq 客戶端
        
        Args:
            api_key: Groq API Key，若未提供則從環境變數 GROQ_API_KEY 讀取
            model: 使用的模型名稱
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY', '')
        self.model = model
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _make_request(self, messages: list, temperature: float = 0.1) -> Optional[Dict]:
        """
        發送 API 請求到 Groq
        
        Args:
            messages: 對話訊息列表
            temperature: 溫度參數
            
        Returns:
            API 回應資料，失敗時返回 None
        """
        if not self.api_key:
            raise ValueError("Groq API Key 未設定")

        # ✅ 1. 確認 URL 完整無誤 (必須包含 /openai/)
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        # ✅ 2. 確認 Header 帶有 "Bearer " (注意有空格)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,  # 例如 "llama-3.3-70b-versatile"
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}  # 強制輸出 JSON
        }

        for attempt in range(self.max_retries):
            try:
                # ✅ 3. 使用 json=payload 讓 requests 自動處理編碼
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 404:
                    # ✅ 關鍵修正：印出 Groq 回傳的具體錯誤訊息與當前使用的模型名稱
                    logger.error(f"Groq 404 錯誤詳情：{response.text}")
                    logger.error(f"當前嘗試使用的模型名稱：{self.model}")
                    return None
                    
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                logger.warning(f"Groq 請求失敗 (Attempt {attempt + 1}): {e}")
                time.sleep(self.retry_delay)
            
        return None
    
    def _render_template(self, template: str, data: dict) -> str:
        """逐鍵替換佔位符，避免模板中的 JSON 範例大括號被 format() 誤判"""
        rendered = template
        for key, value in data.items():
            rendered = rendered.replace('{' + key + '}', str(value))
        return rendered
    
    def _clean_stock_data(self, stock_data: Dict) -> Dict:
        """
        🔴 P0 修正：清理股票數據，處理缺失值
        
        【數據缺失處理規則】（最高優先）
        - 任何欄位為 "-"、null、空字串時：
          1. 絕對不得視為 0 或負面證據
          2. 僅用「有值的欄位」評分
          3. 在理由末尾標註「缺失欄位：xx」
        - 只有當欄位「有值且為零或負」時，才可作為負面證據
        
        Args:
            stock_data: 原始股票數據字典
            
        Returns:
            清理後的數據字典
        """
        cleaned = {}
        missing_fields = []
        
        for key, value in stock_data.items():
            # 檢查是否為缺失值
            if value is None or value == '-' or value == '':
                missing_fields.append(key)
                # 標記為「數據缺失」而非 0
                cleaned[key] = '數據缺失'
            else:
                cleaned[key] = value
        
        # 若有缺失欄位，加入標註
        if missing_fields:
            cleaned['_missing_fields'] = missing_fields
        
        return cleaned
    
    def analyze_stock(self, prompt_template: str, stock_data: Dict) -> Optional[Dict]:
        """
        分析股票並返回評分與建議
        
        Args:
            prompt_template: Prompt 模板字串
            stock_data: 股票數據字典
            
        Returns:
            包含 EV 評分、建議、原因的字典
        """
        # 🔴 P0 修正：在發送給 AI 前，先處理缺失數據
        cleaned_data = self._clean_stock_data(stock_data)
        
        # 渲染 Prompt 模板（使用安全替換）
        prompt = self._render_template(prompt_template, cleaned_data)
        
        messages = [
            {
                "role": "system",
                "content": "你是一位擁有 20 年經驗的台股分析師，專精於籌碼面與基本面分析。請僅輸出 JSON 格式，不要輸出其他內容。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response_data = self._make_request(messages)
        
        if not response_data or 'choices' not in response_data:
            return None
        
        content = response_data['choices'][0]['message']['content']
        
        # 解析 JSON 回應
        try:
            # 清理可能的 markdown 標記
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # 驗證必要欄位
            required_fields = ['ev_score', 'recommendation', 'reason']
            for field in required_fields:
                if field not in result:
                    print(f"缺少必要欄位：{field}")
                    return None
            
            return {
                'ev_score': int(result.get('ev_score', 0)),
                'recommendation': result.get('recommendation', '觀望'),
                'reason': result.get('reason', ''),
                'raw_response': content
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤：{e}")
            print(f"原始回應：{content}")
            return None
    
    def judge_regime(self, market_data: Dict) -> Optional[Dict]:
        """
        判斷市場體制
        
        Args:
            market_data: 市場數據字典
            
        Returns:
            包含體制、信心度、理由的字典
        """
        # 讀取體制判斷 Prompt
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'regime_judgment.txt')
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 預設模板 - 使用雙重大括號轉義 JSON 格式
            prompt_template = "你是一位擁有 20 年經驗的台股總經分析師，專精於判斷市場體制。\n\n【市場體制定義】\n- 多頭：大盤在 60 日均線之上，成交量放大，外資連續買超\n- 震盪：大盤在 20-60 日均線間糾結，成交量萎縮，多空拉鋸\n- 空頭：大盤跌破 60 日均線，融資大增但股價下跌，外資連續賣超\n\n【輸入數據】\n{market_data}\n\n【輸出要求】\n請僅輸出以下 JSON 格式：\n{{\"regime\": \"多頭/震盪/空頭\", \"confidence\": \"高/中/低\", \"reason\": \"判斷理由（50 字內）\", \"operation_suggestion\": \"操作建議（30 字內）\", \"risk_level\": \"1-10 分\"}}"
        
        # 格式化市場數據為字串
        market_str = "; ".join([f"{k}: {v}" for k, v in market_data.items()])
        # 使用安全替換避免 JSON 範例大括號被誤判
        prompt = self._render_template(prompt_template, {'market_data': market_str})
        
        messages = [
            {
                "role": "system",
                "content": "你是一位擁有 20 年經驗的台股總經分析師。請僅輸出 JSON 格式。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response_data = self._make_request(messages, temperature=0.2)
        
        if not response_data or 'choices' not in response_data:
            return None
        
        content = response_data['choices'][0]['message']['content']
        
        try:
            # 清理 markdown 標記
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            return {
                'regime': result.get('regime', '震盪'),
                'confidence': result.get('confidence', '中'),
                'reason': result.get('reason', ''),
                'operation_suggestion': result.get('operation_suggestion', ''),
                'risk_level': result.get('risk_level', 5),
                'raw_response': content
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析錯誤：{e}")
            return None
