"""
靜態報告生成器模組
負責將每日分析結果轉換為輕量的 Markdown/HTML 靜態檔案，供 GitHub Pages 託管
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional


def generate_static_review(
    analysis_results: Optional[List[Dict]] = None,
    regime: Optional[Dict] = None,
    output_dir: str = "docs"
) -> str:
    """
    將分析結果輸出為 Markdown 靜態檔案，方便 GitHub Pages 託管
    
    Args:
        analysis_results: 分析結果列表，每個元素包含 code, ev_score, recommendation, reason 等欄位
        regime: 市場體制字典，包含 regime, confidence 等欄位
        output_dir: 輸出目錄，預設為 docs
        
    Returns:
        生成的檔案路徑
    """
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_path = os.path.join(output_dir, f"review_{date_str}.md")
    
    # 若無資料，使用預設值
    if not regime:
        regime = {'regime': '未知', 'confidence': '中'}
    
    if not analysis_results:
        # 嘗試從 data 目錄讀取最新分析結果
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        latest_result = _load_latest_analysis_result(data_dir)
        if latest_result:
            analysis_results = latest_result.get('analysis_results', [])
            regime = latest_result.get('regime', regime)
        else:
            analysis_results = []
    
    # 建立 Markdown 內容
    md_content = f"# 🎯 {date_str} 每日複盤與市場體制分析\n\n"
    md_content += f"**市場體制**: {regime.get('regime', '未知')} | **信心度**: {regime.get('confidence', '中')}\n\n"
    
    if regime.get('reason'):
        md_content += f"**判斷理由**: {regime['reason']}\n\n"
    
    md_content += "## 📊 標的評分摘要\n\n"
    
    if analysis_results:
        md_content += "| 股票代號 | EV 評分 | 建議 | 關鍵理由 |\n"
        md_content += "|---------|--------|------|----------|\n"
        
        for res in analysis_results:
            code = res.get('code', 'N/A')
            score = res.get('ev_score', 0)
            rec = res.get('recommendation', '觀望')
            reason = res.get('reason', '無')
            
            # 截斷理由，避免過長（最多 50 字）
            if len(reason) > 50:
                reason = reason[:50] + "..."
            
            md_content += f"| {code} | {score} | {rec} | {reason} |\n"
    else:
        md_content += "*今日無分析數據*\n"
    
    md_content += "\n---\n\n"
    md_content += f"*本報告由 Sniper System 自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ 靜態報告已生成：{md_path}")
    
    # 同時更新 index.md 作為最新報告入口
    _update_index_md(output_dir, md_path, date_str, regime, analysis_results)
    
    return md_path


def _load_latest_analysis_result(data_dir: str) -> Optional[Dict]:
    """從 data 目錄載入最新的分析結果 JSON"""
    if not os.path.exists(data_dir):
        return None
    
    # 尋找最新的 JSON 檔案
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    if not json_files:
        return None
    
    # 按修改時間排序
    json_files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)), reverse=True)
    latest_file = os.path.join(data_dir, json_files[0])
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 載入分析結果失敗：{e}")
        return None


def _update_index_md(output_dir: str, latest_report_path: str, date_str: str, 
                     regime: Dict, analysis_results: List[Dict]) -> None:
    """更新 index.md 作為報告索引頁面"""
    index_path = os.path.join(output_dir, "index.md")
    
    # 讀取現有索引或建立新的
    history_content = ""
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 保留歷史記錄（在第一個 ## 之後的內容）
            if "## 📜 歷史報告" in content:
                parts = content.split("## 📜 歷史報告")
                if len(parts) > 1:
                    history_content = "## 📜 歷史報告" + parts[1]
    
    # 建立新的索引內容
    index_content = f"""# 📈 Sniper System 每日複盤報告

## 🎯 最新報告 ({date_str})

**市場體制**: {regime.get('regime', '未知')} | **信心度**: {regime.get('confidence', '中')}

### 今日重點標的

"""
    
    # 列出前 5 個高分標的
    if analysis_results:
        top_picks = sorted(analysis_results, key=lambda x: x.get('ev_score', 0), reverse=True)[:5]
        for pick in top_picks:
            code = pick.get('code', 'N/A')
            score = pick.get('ev_score', 0)
            rec = pick.get('recommendation', '觀望')
            index_content += f"- **{code}**: EV 評分 {score} - {rec}\n"
    else:
        index_content += "*今日無分析數據*\n"
    
    index_content += f"\n[查看完整報告]({os.path.basename(latest_report_path)})\n\n"
    
    # 添加歷史記錄區段
    if not history_content:
        history_content = "\n## 📜 歷史報告\n\n"
    
    # 添加新連結到歷史記錄開頭
    history_content = history_content.replace(
        "## 📜 歷史報告",
        f"## 📜 歷史報告\n\n- [{date_str} 每日複盤]({os.path.basename(latest_report_path)})"
    )
    
    index_content += history_content
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"📑 索引頁面已更新：{index_path}")


def generate_html_report(
    analysis_results: Optional[List[Dict]] = None,
    regime: Optional[Dict] = None,
    output_dir: str = "docs"
) -> str:
    """
    生成 HTML 格式的靜態報告
    
    Args:
        analysis_results: 分析結果列表
        regime: 市場體制字典
        output_dir: 輸出目錄
        
    Returns:
        生成的 HTML 檔案路徑
    """
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    html_path = os.path.join(output_dir, f"report_{date_str}.html")
    
    if not regime:
        regime = {'regime': '未知', 'confidence': '中'}
    
    if not analysis_results:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        latest_result = _load_latest_analysis_result(data_dir)
        if latest_result:
            analysis_results = latest_result.get('analysis_results', [])
            regime = latest_result.get('regime', regime)
        else:
            analysis_results = []
    
    # 建立表格行
    table_rows = ""
    if analysis_results:
        for res in analysis_results:
            code = res.get('code', 'N/A')
            score = res.get('ev_score', 0)
            rec = res.get('recommendation', '觀望')
            reason = res.get('reason', '無')[:80]
            
            # 根據評分設定顏色
            color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"
            
            table_rows += f"""
            <tr>
                <td>{code}</td>
                <td><span style="color: {color}; font-weight: bold;">{score}</span></td>
                <td>{rec}</td>
                <td>{reason}</td>
            </tr>
            """
    else:
        table_rows = "<tr><td colspan='4'>今日無分析數據</td></tr>"
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sniper System 每日複盤 - {date_str}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .regime-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 {date_str} 每日複盤與市場體制分析</h1>
        
        <p>
            <span class="regime-badge">{regime.get('regime', '未知')}</span>
            <strong>信心度</strong>: {regime.get('confidence', '中')}
        </p>
        
        {f"<p><em>判斷理由</em>: {regime.get('reason', '')}</p>" if regime.get('reason') else ""}
        
        <h2>📊 標的評分摘要</h2>
        
        <table>
            <thead>
                <tr>
                    <th>股票代號</th>
                    <th>EV 評分</th>
                    <th>建議</th>
                    <th>關鍵理由</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>本報告由 Sniper System 自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 報告已生成：{html_path}")
    return html_path


if __name__ == "__main__":
    # 測試用範例資料
    test_results = [
        {'code': '2330', 'ev_score': 85, 'recommendation': '買進', 'reason': '營收成長強勁，投信連續買超'},
        {'code': '2454', 'ev_score': 72, 'recommendation': '買進', 'reason': '技術面突破，融資下降'},
        {'code': '1301', 'ev_score': 45, 'recommendation': '觀望', 'reason': '景氣循環下行，等待反轉訊號'},
    ]
    
    test_regime = {
        'regime': '多頭',
        'confidence': '高',
        'reason': '大盤站穩月線，成交量放大，外資連續買超'
    }
    
    generate_static_review(test_results, test_regime)
    generate_html_report(test_results, test_regime)
