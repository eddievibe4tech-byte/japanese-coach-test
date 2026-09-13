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

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 Groq 客戶端

        Args:
            api_key: Groq API Key，若未提供則從環境變數 GROQ_API_KEY 讀取
            model: 使用的模型名稱，若未提供則從環境變數 GROQ_MODEL 讀取，預設為 qwen/qwen3.6-27b
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY', '')
        self.model = model or os.getenv('GROQ_MODEL', 'qwen/qwen3.6-27b')
        self.base_url = 'https://api.groq.com/openai/v1/chat/completions'
        self.max_retries = 3
        self.retry_delay = 2.0

    def _make_request(self, messages: list, temperature: float = 0.3) -> Optional[Dict]:
        """
        發送 API 請求到 Groq

        Args:
            messages: 對話訊息列表
            temperature: 溫度參數（降低至 0.3 讓輸出更穩定）

        Returns:
            API 回應資料，失敗時返回 None
        """
        if not self.api_key:
            raise ValueError("Groq API Key 未設定")

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)

                if response.status_code != 200:
                    logger.error(f"Groq API 失敗 (HTTP {response.status_code}):")
                    logger.error(f"URL: {url}")
                    logger.error(f"Model: {self.model}")
                    logger.error(f"Response: {response.text}")
                    return None

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

    def analyze_stock(self, prompt_template: str, stock_data: Dict) -> Optional[Dict]:
        """
        分析股票並返回評分與建議

        Args:
            prompt_template: Prompt 模板字串
            stock_data: 股票數據字典

        Returns:
            包含 EV 評分、建議、原因的字典
        """
        prompt = self._render_template(prompt_template, stock_data)

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

        logger.info(f"發送請求到 Groq，模型：{self.model}")
        response_data = self._make_request(messages)

        if not response_data or 'choices' not in response_data:
            logger.error(f"Groq 未回傳有效數據")
            return None

        content = response_data['choices'][0]['message']['content']
        logger.info(f"Groq 回傳內容長度：{len(content)} 字元")

        # 關鍵修正 1：處理 </think> 標籤 - 提取標籤後的 JSON
        json_candidate = content
        if '</think>' in content:
            json_candidate = content.split('</think>')[-1].strip()
            logger.info(f"已提取 </think> 後的內容，長度：{len(json_candidate)} 字元")

        # 關鍵修正 2：尋找最後一個 '{' 和最後一個 '}' 之間的內容
        start_idx = json_candidate.rfind('{')
        end_idx = json_candidate.rfind('}')

        json_str = None
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = json_candidate[start_idx:end_idx+1]
            logger.info(f"成功提取 JSON 區塊（長度：{len(json_str)}）")
        else:
            logger.warning("無法在回應中找到有效的 JSON 區塊")
            logger.warning(f"原始內容結尾：...{content[-500:]}")
            return None

        # 解析 JSON 回應
        try:
            content_to_parse = json_str.strip()

            # 移除可能的 Markdown 標記
            if content_to_parse.startswith('```'):
                content_to_parse = content_to_parse.split('```')[1] if '```' in content_to_parse[3:] else content_to_parse[3:]
                content_to_parse = content_to_parse.rsplit('```')[0] if '```' in content_to_parse else content_to_parse
                content_to_parse = content_to_parse.strip()

            # 嘗試多種 JSON 解析方式
            try:
                result = json.loads(content_to_parse)
            except json.JSONDecodeError:
                import re
                content_clean = re.sub(r'^\s*[\{"]\s*', '{', content_to_parse)
                content_clean = re.sub(r'\s*[\}"]\s*$', '}', content_clean)
                result = json.loads(content_clean)

            # 驗證必要欄位並加入預設值
            if 'ev_score' not in result:
                logger.warning("缺少 ev_score 欄位")
                result['ev_score'] = 50
            if 'recommendation' not in result:
                logger.warning("缺少 recommendation 欄位")
                result['recommendation'] = "觀望"
            if 'reason' not in result:
                logger.warning("缺少 reason 欄位")
                result['reason'] = "AI 分析失敗"

            logger.info(f"✅ 解析成功：EV={result.get('ev_score')}, 建議={result.get('recommendation')}")

            return {
                'ev_score': int(result.get('ev_score', 50)),
                'recommendation': result.get('recommendation', '觀望'),
                'reason': result.get('reason', 'AI 分析失敗'),
                'raw_response': content
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失敗：{e}")
            logger.error(f"提取到的字串：{json_str[:200] if json_str else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"❌ 解析 Groq 回應時出錯：{e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def judge_regime(self, market_data: Dict) -> Optional[Dict]:
        """
        判斷市場體制

        Args:
            market_data: 市場數據字典

        Returns:
            包含體制、信心度、理由的字典
        """
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'regime_judgment.txt')

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            prompt_template = "你是一位擁有 20 年經驗的台股總經分析師，專精於判斷市場體制。\n\n【市場體制定義】\n- 多頭：大盤在 60 日均線之上，成交量放大，外資連續買超\n- 震盪：大盤在 20-60 日均線間糾結，成交量萎縮，多空拉鋸\n- 空頭：大盤跌破 60 日均線，融資大增但股價下跌，外資連續賣超\n\n【輸入數據】\n{market_data}\n\n【輸出要求】\n請僅輸出以下 JSON 格式：\n{{\"regime\": \"多頭/震盪/空頭\", \"confidence\": \"高/中/低\", \"reason\": \"判斷理由（50 字內）\", \"operation_suggestion\": \"操作建議（30 字內）\", \"risk_level\": \"1-10 分\"}}"

        market_str = "; ".join([f"{k}: {v}" for k, v in market_data.items()])
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
            content = content.strip()
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()

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
            logger.error(f"JSON 解析錯誤：{e}")
            logger.error(f"原始內容：{content}")
            return None
        except Exception as e:
            logger.error(f"解析 Groq 回應時出錯：{e}")
            return None
