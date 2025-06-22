"""
レポート生成機能
月次レポートとブログ用コンテンツを自動生成
"""

import json
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.conf import settings
import gspread
from google.oauth2.service_account import Credentials
import base64
from io import BytesIO
import pandas as pd

logger = logging.getLogger(__name__)

def get_gspread_client():
    """Google Sheetsクライアントを取得"""
    try:
        credentials_info = getattr(settings, 'GOOGLE_SHEETS_CREDENTIALS', None)
        if credentials_info:
            credentials = Credentials.from_service_account_info(
                credentials_info, scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            return gspread.authorize(credentials)
        else:
            logger.warning("Google Sheets credentials not configured")
            return None
    except Exception as e:
        logger.error(f"Google Sheets client initialization error: {e}")
        return None

def get_spreadsheet():
    """スプレッドシートを取得"""
    client = get_gspread_client()
    if not client:
        return None
        
    try:
        spreadsheet_id = getattr(settings, 'GOOGLE_SHEETS_ID', None)
        if spreadsheet_id:
            return client.open_by_key(spreadsheet_id)
        else:
            spreadsheet_name = getattr(settings, 'GOOGLE_SHEETS_NAME', 'Portfolio Data')
            return client.open(spreadsheet_name)
    except Exception as e:
        logger.error(f"Spreadsheet access error: {e}")
        return None

@require_http_methods(["GET"])
def generate_report(request, month):
    """
    指定された月の投資レポートを生成
    
    GET /api/generate_report/2024-01/
    """
    try:
        # 月の形式を検証
        try:
            report_date = datetime.strptime(month, '%Y-%m')
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid month format. Use YYYY-MM'
            }, status=400)
        
        # レポートデータを生成
        report_data = generate_monthly_report_data(month)
        
        if not report_data['success']:
            return JsonResponse({
                'success': False,
                'error': report_data['error']
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'data': report_data['data'],
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def generate_blog_content(request, month):
    """
    ブログ用コンテンツを生成
    
    GET /api/generate_blog_content/2024-01/?format=markdown&include_images=true
    """
    try:
        format_type = request.GET.get('format', 'html')  # html, markdown, json
        include_images = request.GET.get('include_images', 'false').lower() == 'true'
        
        # レポートデータを取得
        report_data = generate_monthly_report_data(month)
        
        if not report_data['success']:
            return JsonResponse({
                'success': False,
                'error': report_data['error']
            }, status=500)
        
        # フォーマットに応じてコンテンツを生成
        if format_type == 'markdown':
            content = generate_markdown_content(report_data['data'], include_images)
            return HttpResponse(
                content,
                content_type='text/markdown',
                headers={'Content-Disposition': f'attachment; filename="report-{month}.md"'}
            )
        elif format_type == 'json':
            return JsonResponse({
                'success': True,
                'data': {
                    'title': f'{month} 投資成績レポート',
                    'content': generate_html_content(report_data['data'], include_images),
                    'excerpt': generate_excerpt(report_data['data']),
                    'tags': ['投資', 'ポートフォリオ', '月次レポート', '株式'],
                    'category': 'investment',
                    'meta': {
                        'month': month,
                        'total_profit': report_data['data']['summary']['total_profit'],
                        'monthly_profit': report_data['data']['summary']['monthly_profit'],
                        'portfolio_count': len(report_data['data']['portfolio'])
                    }
                }
            })
        else:  # HTML
            content = generate_html_content(report_data['data'], include_images)
            return HttpResponse(
                content,
                content_type='text/html',
                headers={'Content-Disposition': f'attachment; filename="report-{month}.html"'}
            )
        
    except Exception as e:
        logger.error(f"Blog content generation error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def get_report_templates(request):
    """
    利用可能なレポートテンプレートを取得
    
    GET /api/get_report_templates/
    """
    templates = [
        {
            'id': 'standard',
            'name': '標準レポート',
            'description': 'サマリー、ポートフォリオ詳細、所感を含む基本的なレポート',
            'sections': ['summary', 'portfolio', 'chart', 'commentary']
        },
        {
            'id': 'detailed',
            'name': '詳細レポート',
            'description': '詳細な分析とトピックスを含む包括的なレポート',
            'sections': ['summary', 'portfolio', 'chart', 'analysis', 'topics', 'commentary']
        },
        {
            'id': 'simple',
            'name': 'シンプルレポート',
            'description': 'サマリーとポートフォリオのみの簡潔なレポート',
            'sections': ['summary', 'portfolio']
        },
        {
            'id': 'blog',
            'name': 'ブログ用レポート',
            'description': 'ブログ投稿に最適化されたレポート',
            'sections': ['summary', 'chart', 'highlights', 'commentary']
        }
    ]
    
    return JsonResponse({
        'success': True,
        'templates': templates
    })

def generate_monthly_report_data(month: str) -> Dict[str, Any]:
    """
    月次レポートデータを生成
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return {
                'success': False,
                'error': 'Unable to access spreadsheet'
            }
        
        # ポートフォリオデータを取得
        portfolio_data = get_portfolio_data(spreadsheet)
        
        # 価格履歴データを取得
        price_history = get_price_history(spreadsheet, month)
        
        # サマリーを計算
        summary = calculate_summary(portfolio_data, price_history, month)
        
        # トピックスを取得
        topics = get_monthly_topics(month)
        
        # 所感を生成
        commentary = generate_commentary(summary, portfolio_data, month)
        
        return {
            'success': True,
            'data': {
                'month': month,
                'summary': summary,
                'portfolio': portfolio_data,
                'price_history': price_history,
                'topics': topics,
                'commentary': commentary,
                'generated_at': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Monthly report data generation error: {e}")
        return {
            'success': False,
            'error': f'Failed to generate report data: {str(e)}'
        }

def get_portfolio_data(spreadsheet) -> List[Dict[str, Any]]:
    """
    ポートフォリオデータを取得
    """
    try:
        portfolio_sheet = spreadsheet.worksheet('Portfolio')
        all_values = portfolio_sheet.get_all_values()
        
        portfolio_data = []
        for row in all_values[1:]:  # ヘッダーをスキップ
            if len(row) >= 7 and row[0]:  # 有効なデータ行
                profit = float(row[6]) if row[6] else 0
                market_value = float(row[5]) if row[5] else 0
                avg_price = float(row[3]) if row[3] else 0
                profit_rate = (profit / (market_value - profit)) * 100 if (market_value - profit) > 0 else 0
                
                portfolio_data.append({
                    'ticker': row[0],
                    'name': row[1],
                    'quantity': int(row[2]) if row[2] else 0,
                    'avg_price': avg_price,
                    'current_price': float(row[4]) if row[4] else 0,
                    'market_value': market_value,
                    'profit': profit,
                    'profit_rate': profit_rate
                })
        
        return portfolio_data
        
    except Exception as e:
        logger.error(f"Portfolio data retrieval error: {e}")
        return []

def get_price_history(spreadsheet, month: str) -> List[Dict[str, Any]]:
    """
    価格履歴データを取得
    """
    try:
        price_sheet = spreadsheet.worksheet('Price Data')
        all_values = price_sheet.get_all_values()
        
        # 指定月のデータをフィルタ
        month_start = f"{month}-01"
        month_end = f"{month}-31"  # 簡易的な月末
        
        price_history = []
        for row in all_values[1:]:  # ヘッダーをスキップ
            if len(row) >= 4 and row[0]:
                if month_start <= row[0] <= month_end:
                    price_history.append({
                        'date': row[0],
                        'ticker': row[1],
                        'name': row[2],
                        'price': float(row[3]) if row[3] else 0,
                        'quantity': int(row[4]) if len(row) > 4 and row[4] else 0,
                        'transaction_type': row[5] if len(row) > 5 else 'update'
                    })
        
        # 日付順にソート
        price_history.sort(key=lambda x: x['date'])
        
        return price_history
        
    except Exception as e:
        logger.error(f"Price history retrieval error: {e}")
        return []

def calculate_summary(portfolio_data: List[Dict], price_history: List[Dict], month: str) -> Dict[str, Any]:
    """
    サマリーデータを計算
    """
    total_value = sum(stock['market_value'] for stock in portfolio_data)
    total_profit = sum(stock['profit'] for stock in portfolio_data)
    total_investment = total_value - total_profit
    
    # 月次変化を計算（簡易版）
    monthly_transactions = [t for t in price_history if t['transaction_type'] in ['buy', 'sell']]
    monthly_profit = sum(
        t['quantity'] * t['price'] * (-1 if t['transaction_type'] == 'sell' else 1)
        for t in monthly_transactions
    )
    
    # 前月比計算（ダミーデータ）
    monthly_change = 15.2 if monthly_profit > 0 else -8.3
    total_return = (total_profit / total_investment) * 100 if total_investment > 0 else 0
    
    return {
        'total_value': total_value,
        'total_profit': total_profit,
        'total_investment': total_investment,
        'monthly_profit': monthly_profit,
        'monthly_change': monthly_change,
        'total_return': total_return,
        'portfolio_count': len(portfolio_data),
        'positive_stocks': len([s for s in portfolio_data if s['profit'] > 0]),
        'negative_stocks': len([s for s in portfolio_data if s['profit'] < 0])
    }

def get_monthly_topics(month: str) -> List[Dict[str, Any]]:
    """
    月次トピックスを取得（ダミーデータ）
    実際の実装では外部ニュースAPIや手動入力データから取得
    """
    topics = [
        {
            'date': f'{month}-15',
            'title': 'テクノロジー株の上昇トレンド',
            'content': 'AI関連銘柄を中心にテクノロジー株が好調に推移しています。'
        },
        {
            'date': f'{month}-22',
            'title': '決算シーズンの影響',
            'content': '好決算を発表した企業の株価が大きく上昇しました。'
        }
    ]
    
    return topics

def generate_commentary(summary: Dict, portfolio_data: List[Dict], month: str) -> str:
    """
    所感を自動生成
    """
    positive_count = summary['positive_stocks']
    total_count = summary['portfolio_count']
    monthly_profit = summary['monthly_profit']
    
    if monthly_profit > 0:
        performance = "好調"
        trend = "上昇基調"
    else:
        performance = "軟調"
        trend = "調整局面"
    
    commentary = f"""今月は全体的に{performance}な結果となりました。

保有{total_count}銘柄中{positive_count}銘柄がプラスとなり、
ポートフォリオ全体では{trend}で推移しています。

特に注目すべき銘柄の動向や市場環境の変化について、
継続的にモニタリングを行っていきます。

来月も長期的な視点を維持しながら、
バランスの取れた投資を継続していく予定です。"""
    
    return commentary

def generate_markdown_content(report_data: Dict, include_images: bool = False) -> str:
    """
    Markdown形式のコンテンツを生成
    """
    month = report_data['month']
    summary = report_data['summary']
    portfolio = report_data['portfolio']
    commentary = report_data['commentary']
    
    content = f"""# {month} 投資成績レポート

> ポケモン世代の投資ブログ - Monthly Report  
> Generated on {datetime.now().strftime('%Y年%m月%d日')}

## 📊 今月のサマリー

| 項目 | 金額 | 変化率 |
|------|------|--------|
| 今月の損益 | {'+' if summary['monthly_profit'] >= 0 else ''}¥{summary['monthly_profit']:,.0f} | {'+' if summary['monthly_change'] >= 0 else ''}{summary['monthly_change']:.1f}% |
| 累計損益 | {'+' if summary['total_profit'] >= 0 else ''}¥{summary['total_profit']:,.0f} | {'+' if summary['total_return'] >= 0 else ''}{summary['total_return']:.1f}% |
| 総資産評価額 | ¥{summary['total_value']:,.0f} | - |
| 投資元本 | ¥{summary['total_investment']:,.0f} | - |

"""

    if include_images:
        content += """## 📈 資産推移グラフ

![資産推移グラフ](chart-image.png)

"""

    content += """## 💼 保有銘柄詳細

| 銘柄 | 保有数 | 取得単価 | 現在価格 | 評価額 | 損益 | 損益率 |
|------|--------|----------|----------|--------|------|--------|
"""

    for stock in portfolio:
        profit_sign = '+' if stock['profit'] >= 0 else ''
        rate_sign = '+' if stock['profit_rate'] >= 0 else ''
        content += f"| {stock['name']} ({stock['ticker']}) | {stock['quantity']}株 | ¥{stock['avg_price']:,.0f} | ¥{stock['current_price']:,.0f} | ¥{stock['market_value']:,.0f} | {profit_sign}¥{stock['profit']:,.0f} | {rate_sign}{stock['profit_rate']:.1f}% |\n"

    content += f"""

## 💭 今月の所感

{commentary}

---

*このレポートは Vue.js Portfolio Tracker で自動生成されました。*

### タグ
#投資 #ポートフォリオ #月次レポート #株式投資 #{month.replace('-', '年')}月
"""

    return content

def generate_html_content(report_data: Dict, include_images: bool = False) -> str:
    """
    HTML形式のコンテンツを生成
    """
    month = report_data['month']
    summary = report_data['summary']
    portfolio = report_data['portfolio']
    commentary = report_data['commentary']
    
    # HTMLテンプレートを使用してコンテンツを生成
    context = {
        'month': month,
        'summary': summary,
        'portfolio': portfolio,
        'commentary': commentary,
        'include_images': include_images,
        'generated_date': datetime.now().strftime('%Y年%m月%d日')
    }
    
    try:
        # Djangoテンプレートを使用
        html_content = render_to_string('report_template.html', context)
        return html_content
    except Exception:
        # テンプレートが見つからない場合は簡単なHTMLを生成
        return generate_simple_html(report_data, include_images)

def generate_simple_html(report_data: Dict, include_images: bool = False) -> str:
    """
    シンプルなHTML形式のコンテンツを生成
    """
    month = report_data['month']
    summary = report_data['summary']
    portfolio = report_data['portfolio']
    commentary = report_data['commentary']
    
    html = f"""
<div class="investment-report">
    <header class="report-header">
        <h1>{month} 投資成績レポート</h1>
        <p class="subtitle">ポケモン世代の投資ブログ - Monthly Report</p>
    </header>
    
    <section class="summary-section">
        <h2>📊 今月のサマリー</h2>
        <div class="summary-grid">
            <div class="summary-card highlight">
                <h3>今月の損益</h3>
                <p class="amount {'positive' if summary['monthly_profit'] >= 0 else 'negative'}">
                    {'+' if summary['monthly_profit'] >= 0 else ''}¥{summary['monthly_profit']:,.0f}
                </p>
                <p class="change">前月比 {'+' if summary['monthly_change'] >= 0 else ''}{summary['monthly_change']:.1f}%</p>
            </div>
            
            <div class="summary-card">
                <h3>累計損益</h3>
                <p class="amount {'positive' if summary['total_profit'] >= 0 else 'negative'}">
                    {'+' if summary['total_profit'] >= 0 else ''}¥{summary['total_profit']:,.0f}
                </p>
                <p class="change">{'+' if summary['total_return'] >= 0 else ''}{summary['total_return']:.1f}%</p>
            </div>
            
            <div class="summary-card">
                <h3>総資産評価額</h3>
                <p class="amount">¥{summary['total_value']:,.0f}</p>
                <p class="change">投資元本: ¥{summary['total_investment']:,.0f}</p>
            </div>
        </div>
    </section>
"""

    if include_images:
        html += """
    <section class="chart-section">
        <h2>📈 資産推移</h2>
        <div class="chart-container">
            <img src="chart-image.png" alt="資産推移グラフ" style="max-width: 100%;">
        </div>
    </section>
"""

    html += """
    <section class="portfolio-section">
        <h2>💼 保有銘柄詳細</h2>
        <table class="portfolio-table">
            <thead>
                <tr>
                    <th>銘柄</th>
                    <th>保有数</th>
                    <th>取得単価</th>
                    <th>現在価格</th>
                    <th>評価額</th>
                    <th>損益</th>
                    <th>損益率</th>
                </tr>
            </thead>
            <tbody>
"""

    for stock in portfolio:
        profit_class = 'positive' if stock['profit'] >= 0 else 'negative'
        html += f"""
                <tr>
                    <td><strong>{stock['name']}</strong><br><small>({stock['ticker']})</small></td>
                    <td>{stock['quantity']}株</td>
                    <td>¥{stock['avg_price']:,.0f}</td>
                    <td>¥{stock['current_price']:,.0f}</td>
                    <td>¥{stock['market_value']:,.0f}</td>
                    <td class="{profit_class}">{'+' if stock['profit'] >= 0 else ''}¥{stock['profit']:,.0f}</td>
                    <td class="{profit_class}">{'+' if stock['profit_rate'] >= 0 else ''}{stock['profit_rate']:.1f}%</td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>
    </section>
    
    <section class="commentary-section">
        <h2>💭 今月の所感</h2>
        <div class="commentary-content">
            {commentary.replace(chr(10), '<br>')}
        </div>
    </section>
    
    <footer class="report-footer">
        <p><small>Generated on {datetime.now().strftime('%Y年%m月%d日')} by Vue.js Portfolio Tracker</small></p>
    </footer>
</div>

<style>
.investment-report {{
    max-width: 800px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: #333;
}}

.report-header {{
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #667eea;
}}

.summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}}

.summary-card {{
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}}

.summary-card.highlight {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}}

.amount {{
    font-size: 1.5em;
    font-weight: bold;
    margin: 10px 0;
}}

.positive {{ color: #28a745; }}
.negative {{ color: #dc3545; }}

.portfolio-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}}

.portfolio-table th,
.portfolio-table td {{
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}}

.portfolio-table th {{
    background-color: #f8f9fa;
    font-weight: 600;
}}

.commentary-content {{
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #667eea;
}}

.report-footer {{
    text-align: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
    color: #666;
}}
</style>
"""

    return html

def generate_excerpt(report_data: Dict) -> str:
    """
    ブログ投稿用の要約を生成
    """
    summary = report_data['summary']
    month = report_data['month']
    
    profit_status = "好調" if summary['monthly_profit'] >= 0 else "軟調"
    
    return f"{month}の投資成績をレポート。今月は{profit_status}な結果となり、" \
           f"月次損益は{'+' if summary['monthly_profit'] >= 0 else ''}{summary['monthly_profit']:,.0f}円、" \
           f"ポートフォリオ全体の評価額は{summary['total_value']:,.0f}円となりました。"