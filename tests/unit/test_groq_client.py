"""
Groq 客戶端單元測試
測試 AI 分析功能與 JSON 解析
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.groq_client import GroqClient


class TestGroqClientInit:
    """測試 GroqClient 初始化"""
    
    def test_init_with_api_key(self):
        """測試提供 API Key 的初始化"""
        client = GroqClient(api_key='test_key')
        assert client.api_key == 'test_key'
        # 預設模型為 qwen/qwen3.6-27b
        assert client.model == "qwen/qwen3.6-27b"
    
    def test_init_custom_model(self):
        """測試自訂模型"""
        client = GroqClient(api_key='test_key', model='custom-model')
        assert client.model == 'custom-model'
    
    def test_init_without_api_key(self, monkeypatch):
        """測試未提供 API Key 時的初始化"""
        monkeypatch.delenv('GROQ_API_KEY', raising=False)
        client = GroqClient()
        assert client.api_key == ''
    
    def test_init_from_env(self, monkeypatch):
        """測試從環境變數讀取 API Key"""
        monkeypatch.setenv('GROQ_API_KEY', 'env_key')
        client = GroqClient()
        assert client.api_key == 'env_key'


class TestMakeRequest:
    """測試 API 請求"""
    
    @patch('src.groq_client.requests.post')
    def test_successful_request(self, mock_post):
        """測試成功的 API 請求"""
        import json
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {'content': json.dumps({"result": "test"})}
            }]
        }
        mock_post.return_value = mock_response
        
        client = GroqClient(api_key='test_key')
        messages = [{'role': 'user', 'content': 'test'}]
        result = client._make_request(messages)
        
        assert result is not None
        assert 'choices' in result
    
    @patch('src.groq_client.requests.post')
    def test_timeout_retry(self, mock_post):
        """測試超時重試"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        client = GroqClient(api_key='test_key', model='test')
        client.max_retries = 2
        client.retry_delay = 0.1
        
        messages = [{'role': 'user', 'content': 'test'}]
        result = client._make_request(messages)
        
        # 重試後應返回 None
        assert result is None
        # 確認呼叫了多次
        assert mock_post.call_count == 2
    
    def test_no_api_key(self):
        """測試未設定 API Key"""
        client = GroqClient(api_key='')
        
        with pytest.raises(ValueError, match="Groq API Key 未設定"):
            client._make_request([])


class TestAnalyzeStock:
    """測試股票分析功能"""
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_analyze_stock_success(self, mock_request):
        """測試成功的股票分析"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '{"ev_score": 85, "recommendation": "積極買入", "reason": "基本面佳"}'
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        prompt_template = "分析股票 {code}"
        stock_data = {'code': '2330'}
        
        result = client.analyze_stock(prompt_template, stock_data)
        
        assert result is not None
        assert result['ev_score'] == 85
        assert result['recommendation'] == "積極買入"
        assert result['reason'] == "基本面佳"
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_analyze_stock_with_markdown(self, mock_request):
        """測試含 Markdown 標記的回應"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '```json\n{"ev_score": 75, "recommendation": "觀望", "reason": "中性"}\n```'
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        prompt_template = "分析股票 {code}"
        stock_data = {'code': '2330'}
        
        result = client.analyze_stock(prompt_template, stock_data)
        
        assert result is not None
        assert result['ev_score'] == 75
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_analyze_stock_missing_fields(self, mock_request):
        """測試缺少必要欄位時的預設值補齊機制"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '{"ev_score": 80}'  # 缺少 recommendation 和 reason
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        prompt_template = "分析股票 {code}"
        stock_data = {'code': '2330'}
        
        result = client.analyze_stock(prompt_template, stock_data)
        
        # ✅ 修正：預期應回傳帶有預設值的字典，而非 None
        assert result is not None
        assert result['ev_score'] == 80
        assert result['recommendation'] == "觀望"
        assert result['reason'] == "AI 分析失敗"
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_analyze_stock_invalid_json(self, mock_request):
        """測試無效 JSON"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '這不是 JSON 格式'
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        prompt_template = "分析股票 {code}"
        stock_data = {'code': '2330'}
        
        result = client.analyze_stock(prompt_template, stock_data)
        
        assert result is None
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_analyze_stock_api_failure(self, mock_request):
        """測試 API 失敗"""
        mock_request.return_value = None
        
        client = GroqClient(api_key='test_key')
        prompt_template = "分析股票 {code}"
        stock_data = {'code': '2330'}
        
        result = client.analyze_stock(prompt_template, stock_data)
        
        assert result is None


class TestJudgeRegime:
    """測試市場體制判斷"""
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_judge_regime_success(self, mock_request):
        """測試成功的體制判斷"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '{"regime": "震盪", "confidence": "高", "reason": "大盤整理", "operation_suggestion": "區間操作", "risk_level": 5}'
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        market_data = {'twii': 18000, 'volume': 3000}
        
        result = client.judge_regime(market_data)
        
        assert result is not None
        assert result['regime'] == "震盪"
        assert result['confidence'] == "高"
        assert result['risk_level'] == 5
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_judge_regime_default_values(self, mock_request):
        """測試預設值處理"""
        mock_request.return_value = {
            'choices': [{
                'message': {
                    'content': '{}'  # 空物件，應使用預設值
                }
            }]
        }
        
        client = GroqClient(api_key='test_key')
        market_data = {'twii': 18000}
        
        result = client.judge_regime(market_data)
        
        assert result is not None
        assert result['regime'] == "震盪"  # 預設值
        assert result['confidence'] == "中"  # 預設值
        assert result['risk_level'] == 5  # 預設值
    
    @patch('src.groq_client.GroqClient._make_request')
    def test_judge_regime_api_failure(self, mock_request):
        """測試 API 失敗"""
        mock_request.return_value = None
        
        client = GroqClient(api_key='test_key')
        market_data = {'twii': 18000}
        
        result = client.judge_regime(market_data)
        
        assert result is None
