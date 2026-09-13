#!/bin/bash
# ============================================
# 狙擊手系統 - 專案初始化腳本
# 使用方式: chmod +x setup_project.sh && ./setup_project.sh
# ============================================

set -e

echo "🎯 正在初始化狙擊手系統..."

# 建立目錄結構
mkdir -p specs/features
mkdir -p src
mkdir -p tests/unit
mkdir -p tests/bdd/steps
mkdir -p data
mkdir -p prompts
mkdir -p .github/workflows

# 建立 __init__.py
touch src/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/bdd/__init__.py
touch tests/bdd/steps/__init__.py

echo "✅ 目錄結構建立完成"

# ============================================
# 1. 依賴文件
# ============================================

cat > requirements.txt << 'EOF'
requests>=2.31.0
python-dotenv>=1.0.0
EOF

cat > requirements-dev.txt << 'EOF'
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
behave>=1.2.6
responses>=0.24.0
freezegun>=1.2.0
EOF

echo "✅ 依賴文件建立完成"

# ============================================
# 2. pytest 設定
# ============================================

cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: 單元測試
    integration: 整合測試
    slow: 慢速測試
    api: 需要外部 API 的測試
EOF

cat > behave.ini << 'EOF'
[behave]
paths = specs/features
format = pretty
show_timings = true
stdout_capture = true
stderr_capture = true
EOF

echo "✅ 測試設定建立完成"

# ============================================
# 3. .gitignore
# ============================================

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 測試
htmlcov/
.coverage
.coverage.*
.pytest_cache/
.tox/

# 環境變數
.env
.venv
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 系統
.DS_Store
Thumbs.db

# 敏感資訊
*_api_key*
*_token*
*.secret
EOF

echo "✅ .gitignore 建立完成"

# ============================================
# 4. 初始數據文件
# ============================================

cat > data/regime.json << 'EOF'
{
  "current_regime": "震盪",
  "trade_size": 5000,
  "target_rr": 2,
  "max_positions": 3,
  "max_risk_percent": 2,
  "industry_limit_percent": 40,
  "leverage_limit": 5,
  "volatility_limit": 30,
  "last_updated": ""
}
EOF

cat > data/stock_pool.json << 'EOF'
{
  "stocks": [
    {
      "code": "2330",
      "name": "台積電",
      "industry": "半導體",
      "topic": "AI/先進製程",
      "ex_div_date": "",
      "notes": "權值股，流動性最佳"
    },
    {
      "code": "2308",
      "name": "台達電",
      "industry": "電子",
      "topic": "AI 電源/散熱",
      "ex_div_date": "",
      "notes": "電力題材"
    },
    {
      "code": "2454",
      "name": "聯發科",
      "industry": "半導體",
      "topic": "邊緣 AI",
      "ex_div_date": "",
      "notes": "IC 設計"
    },
    {
      "code": "2881",
      "name": "富邦金",
      "industry": "金融",
      "topic": "高利率受惠",
      "ex_div_date": "",
      "notes": "金融股"
    }
  ]
}
EOF

cat > data/telemetry.json << 'EOF'
{
  "records": [],
  "metadata": {
    "created_at": "",
    "total_records": 0
  }
}
EOF

cat > data/prompt_history.json << 'EOF'
{
  "current_version": 1,
  "optimizations": []
}
EOF

cat > data/performance_metrics.json << 'EOF'
{
  "total_predictions": 0,
  "accuracy_rate": 0,
  "current_version": 1,
  "version_stats": {},
  "last_updated": ""
}
EOF

echo "✅ 初始數據文件建立完成"

# ============================================
# 5. Prompt 模板
# ============================================

cat > prompts/main_analysis.txt << 'PROMPT_EOF'
你是一位擁有 20 年經驗的台股分析師，專精於籌碼面與基本面分析。

【台股邏輯範例】
- 融資大減 + 股價不跌 = 散戶洗盤，籌碼乾淨 (利多)
- 投信連買 + 營收 YoY > 20% = 法人看好，基本面佳 (利多)
- 波動率 > 30% = 權證時間價值流失快，風險高 (利空)
- 接近除息日 (<7 天) = 避免觀望期，除息後再戰 (中性)

【任務】
評估以下標的的狙擊價值。

【輸入數據】
- 股票代號：{code}
- 股票名稱：{name}
- 產業：{industry}
- 市場體制：{regime}
- 月營收年增率：{revenue_yoy}%
- 投信連續買超：{inst_buy_days}天
- 融資增減：{margin_change}張
- 近 5 日漲跌幅：{change_5d}%
- 20 日波動率：{volatility}%
- 距除息天數：{ex_div_days}天

【輸出要求】
請僅輸出以下 JSON 格式，不要輸出其他內容：
{
  "ev_score": "0-100",
  "recommendation": "積極買入/觀望/避開",
  "reason": "50 字內"
}
PROMPT_EOF

cat > prompts/regime_judgment.txt << 'PROMPT_EOF'
你是一位擁有 20 年經驗的台股總經分析師，專精於判斷市場體制。

【市場體制定義】
- 多頭：大盤在 60 日均線之上，成交量放大，外資連續買超
- 震盪：大盤在 20-60 日均線間糾結，成交量萎縮，多空拉鋸
- 空頭：大盤跌破 60 日均線，融資大增但股價下跌，外資連續賣超

【輸入數據】
{market_data}

【輸出要求】
請僅輸出以下 JSON 格式：
{
  "regime": "多頭/震盪/空頭",
  "confidence": "高/中/低",
  "reason": "判斷理由（50 字內）",
  "operation_suggestion": "操作建議（30 字內）",
  "risk_level": "1-10 分"
}
PROMPT_EOF

echo "✅ Prompt 模板建立完成"

# ============================================
# 提示訊息
# ============================================

echo ""
echo "============================================"
echo "🎯 專案初始化完成！"
echo "============================================"
echo ""
echo "📁 目錄結構："
echo "  specs/          - OpenAPI 規格與 BDD Features"
echo "  src/            - 原始碼"
echo "  tests/unit/     - 單元測試"
echo "  tests/bdd/      - BDD 步驟定義"
echo "  data/           - 數據文件"
echo "  prompts/        - Prompt 模板"
echo ""
echo "📋 下一步："
echo "  1. pip install -r requirements-dev.txt"
echo "  2. pytest tests/unit/ -v"
echo "  3. behave"
echo "============================================"
