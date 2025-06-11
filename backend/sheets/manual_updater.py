"""
手動データ更新用API
スプレッドシートのデータを手動で更新するためのAPIエンドポイント
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# Google Sheets API設定
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_gspread_client():
    """Google Sheetsクライアントを取得"""
    try:
        # サービスアカウントキーファイルから認証情報を取得
        # 実際の実装では設定ファイルから取得
        credentials_info = getattr(settings, 'GOOGLE_SHEETS_CREDENTIALS', None)
        if credentials_info:
            credentials = Credentials.from_service_account_info(
                credentials_info, scopes=SCOPES
            )
        else:
            # 開発用のダミー設定
            credentials = None
            logger.warning("Google Sheets credentials not configured")
            
        if credentials:
            return gspread.authorize(credentials)
        else:
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
            # スプレッドシート名で取得（フォールバック）
            spreadsheet_name = getattr(settings, 'GOOGLE_SHEETS_NAME', 'Portfolio Data')
            return client.open(spreadsheet_name)
    except Exception as e:
        logger.error(f"Spreadsheet access error: {e}")
        return None

@csrf_exempt
@require_http_methods(["POST"])
def update_stock_price(request):
    """
    株価データを手動更新
    
    POST /api/update_stock_price/
    {
        "ticker": "7974",
        "name": "任天堂",
        "price": 6500.0,
        "date": "2024-01-15",
        "quantity": 100,
        "transaction_type": "buy" // buy, sell, update
    }
    """
    try:
        data = json.loads(request.body)
        
        # バリデーション
        required_fields = ['ticker', 'name', 'price', 'date']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Required field missing: {field}'
                }, status=400)
        
        ticker = data['ticker']
        name = data['name']
        price = float(data['price'])
        date_str = data['date']
        quantity = data.get('quantity', 0)
        transaction_type = data.get('transaction_type', 'update')
        
        # 日付の検証
        try:
            update_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # スプレッドシート更新
        result = update_spreadsheet_data(
            ticker=ticker,
            name=name,
            price=price,
            update_date=update_date,
            quantity=quantity,
            transaction_type=transaction_type
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Stock price updated successfully',
                'data': {
                    'ticker': ticker,
                    'name': name,
                    'price': price,
                    'date': date_str,
                    'updated_at': datetime.now().isoformat()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Stock price update error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_update_prices(request):
    """
    複数の株価データを一括更新
    
    POST /api/bulk_update_prices/
    {
        "updates": [
            {
                "ticker": "7974",
                "name": "任天堂",
                "price": 6500.0,
                "date": "2024-01-15",
                "quantity": 100,
                "transaction_type": "buy"
            },
            ...
        ]
    }
    """
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])
        
        if not updates:
            return JsonResponse({
                'success': False,
                'error': 'No updates provided'
            }, status=400)
        
        results = []
        errors = []
        
        for i, update_data in enumerate(updates):
            try:
                # 個別の更新処理
                result = update_spreadsheet_data(
                    ticker=update_data['ticker'],
                    name=update_data['name'],
                    price=float(update_data['price']),
                    update_date=datetime.strptime(update_data['date'], '%Y-%m-%d').date(),
                    quantity=update_data.get('quantity', 0),
                    transaction_type=update_data.get('transaction_type', 'update')
                )
                
                if result['success']:
                    results.append({
                        'index': i,
                        'ticker': update_data['ticker'],
                        'status': 'success'
                    })
                else:
                    errors.append({
                        'index': i,
                        'ticker': update_data['ticker'],
                        'error': result['error']
                    })
                    
            except Exception as e:
                errors.append({
                    'index': i,
                    'ticker': update_data.get('ticker', 'unknown'),
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': len(errors) == 0,
            'message': f'Processed {len(results)} updates, {len(errors)} errors',
            'results': results,
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Bulk update error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_monthly_data(request):
    """
    月次データを保存
    
    POST /api/save_monthly_data/
    {
        "month": "2024-01",
        "portfolio_data": [...],
        "summary": {
            "total_value": 1456789,
            "total_profit": 234567,
            "monthly_profit": 45320
        },
        "commentary": "今月の所感..."
    }
    """
    try:
        data = json.loads(request.body)
        
        month = data.get('month')
        portfolio_data = data.get('portfolio_data', [])
        summary = data.get('summary', {})
        commentary = data.get('commentary', '')
        
        if not month:
            return JsonResponse({
                'success': False,
                'error': 'Month is required'
            }, status=400)
        
        # 月次データをスプレッドシートに保存
        result = save_monthly_report_data(
            month=month,
            portfolio_data=portfolio_data,
            summary=summary,
            commentary=commentary
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Monthly data saved successfully',
                'data': {
                    'month': month,
                    'saved_at': datetime.now().isoformat()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)
            
    except Exception as e:
        logger.error(f"Monthly data save error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def update_spreadsheet_data(ticker: str, name: str, price: float, 
                          update_date: date, quantity: int = 0, 
                          transaction_type: str = 'update') -> Dict[str, Any]:
    """
    スプレッドシートのデータを更新
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return {
                'success': False,
                'error': 'Unable to access spreadsheet'
            }
        
        # 価格データシートを取得
        try:
            price_sheet = spreadsheet.worksheet('Price Data')
        except gspread.WorksheetNotFound:
            # シートが存在しない場合は作成
            price_sheet = spreadsheet.add_worksheet(
                title='Price Data', 
                rows=1000, 
                cols=10
            )
            # ヘッダーを設定
            price_sheet.update('1:1', [[
                'Date', 'Ticker', 'Name', 'Price', 'Quantity', 
                'Transaction Type', 'Updated At'
            ]])
        
        # 新しい行を追加
        new_row = [
            update_date.strftime('%Y-%m-%d'),
            ticker,
            name,
            price,
            quantity,
            transaction_type,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        price_sheet.append_row(new_row)
        
        # トランザクションタイプに応じて追加処理
        if transaction_type in ['buy', 'sell']:
            update_portfolio_holdings(
                spreadsheet, ticker, name, quantity, price, transaction_type
            )
        
        return {
            'success': True,
            'message': 'Data updated successfully'
        }
        
    except Exception as e:
        logger.error(f"Spreadsheet update error: {e}")
        return {
            'success': False,
            'error': f'Spreadsheet update failed: {str(e)}'
        }

def update_portfolio_holdings(spreadsheet, ticker: str, name: str, 
                            quantity: int, price: float, transaction_type: str):
    """
    ポートフォリオ保有データを更新
    """
    try:
        # ポートフォリオシートを取得
        try:
            portfolio_sheet = spreadsheet.worksheet('Portfolio')
        except gspread.WorksheetNotFound:
            portfolio_sheet = spreadsheet.add_worksheet(
                title='Portfolio',
                rows=1000,
                cols=8
            )
            # ヘッダーを設定
            portfolio_sheet.update('1:1', [[
                'Ticker', 'Name', 'Quantity', 'Avg Price', 
                'Current Price', 'Market Value', 'Profit/Loss', 'Updated At'
            ]])
        
        # 既存の保有データを検索
        all_values = portfolio_sheet.get_all_values()
        ticker_row = None
        
        for i, row in enumerate(all_values[1:], start=2):  # ヘッダーをスキップ
            if row[0] == ticker:
                ticker_row = i
                break
        
        if ticker_row:
            # 既存データを更新
            current_quantity = int(row[2]) if row[2] else 0
            current_avg_price = float(row[3]) if row[3] else 0
            
            if transaction_type == 'buy':
                # 平均取得価格を計算
                total_cost = (current_quantity * current_avg_price) + (quantity * price)
                new_quantity = current_quantity + quantity
                new_avg_price = total_cost / new_quantity if new_quantity > 0 else 0
            elif transaction_type == 'sell':
                new_quantity = current_quantity - quantity
                new_avg_price = current_avg_price  # 売却時は平均価格は変更しない
            
            # 行を更新
            portfolio_sheet.update_cell(ticker_row, 3, new_quantity)
            portfolio_sheet.update_cell(ticker_row, 4, new_avg_price)
            portfolio_sheet.update_cell(ticker_row, 5, price)  # 現在価格
            portfolio_sheet.update_cell(ticker_row, 8, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
        else:
            # 新しい銘柄を追加
            if transaction_type == 'buy':
                new_row = [
                    ticker,
                    name,
                    quantity,
                    price,  # 平均価格（初回は取得価格）
                    price,  # 現在価格
                    quantity * price,  # 時価総額
                    0,  # 損益（初回は0）
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                portfolio_sheet.append_row(new_row)
        
    except Exception as e:
        logger.error(f"Portfolio update error: {e}")
        raise

def save_monthly_report_data(month: str, portfolio_data: List[Dict], 
                           summary: Dict, commentary: str) -> Dict[str, Any]:
    """
    月次レポートデータを保存
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return {
                'success': False,
                'error': 'Unable to access spreadsheet'
            }
        
        # 月次レポートシートを取得または作成
        sheet_name = f'Report_{month}'
        try:
            report_sheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            report_sheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=10
            )
        
        # サマリーデータを保存
        summary_data = [
            ['Month', month],
            ['Total Value', summary.get('total_value', 0)],
            ['Total Profit', summary.get('total_profit', 0)],
            ['Monthly Profit', summary.get('monthly_profit', 0)],
            ['Commentary', commentary],
            ['Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            [''],  # 空行
            ['Portfolio Data:'],
            ['Ticker', 'Name', 'Quantity', 'Avg Price', 'Current Price', 
             'Market Value', 'Profit/Loss', 'Profit Rate']
        ]
        
        # ポートフォリオデータを追加
        for stock in portfolio_data:
            summary_data.append([
                stock.get('ticker', ''),
                stock.get('name', ''),
                stock.get('quantity', 0),
                stock.get('avgPrice', 0),
                stock.get('currentPrice', 0),
                stock.get('marketValue', 0),
                stock.get('profit', 0),
                stock.get('profitRate', 0)
            ])
        
        # データを一括更新
        report_sheet.clear()
        report_sheet.update('A1', summary_data)
        
        return {
            'success': True,
            'message': f'Monthly report data saved to {sheet_name}'
        }
        
    except Exception as e:
        logger.error(f"Monthly report save error: {e}")
        return {
            'success': False,
            'error': f'Failed to save monthly report: {str(e)}'
        }

@require_http_methods(["GET"])
def get_update_history(request):
    """
    更新履歴を取得
    
    GET /api/get_update_history/?limit=50&ticker=7974
    """
    try:
        limit = int(request.GET.get('limit', 50))
        ticker_filter = request.GET.get('ticker', '')
        
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return JsonResponse({
                'success': False,
                'error': 'Unable to access spreadsheet'
            }, status=500)
        
        try:
            price_sheet = spreadsheet.worksheet('Price Data')
            all_values = price_sheet.get_all_values()
            
            # ヘッダーをスキップして履歴データを取得
            history_data = []
            for row in all_values[1:]:  # ヘッダーをスキップ
                if len(row) >= 7:  # 必要な列数をチェック
                    if not ticker_filter or row[1] == ticker_filter:
                        history_data.append({
                            'date': row[0],
                            'ticker': row[1],
                            'name': row[2],
                            'price': float(row[3]) if row[3] else 0,
                            'quantity': int(row[4]) if row[4] else 0,
                            'transaction_type': row[5],
                            'updated_at': row[6]
                        })
            
            # 日付順（新しい順）にソート
            history_data.sort(key=lambda x: x['updated_at'], reverse=True)
            
            # 制限数を適用
            if limit > 0:
                history_data = history_data[:limit]
            
            return JsonResponse({
                'success': True,
                'data': history_data,
                'count': len(history_data)
            })
            
        except gspread.WorksheetNotFound:
            return JsonResponse({
                'success': True,
                'data': [],
                'count': 0,
                'message': 'No price data sheet found'
            })
        
    except Exception as e:
        logger.error(f"Get update history error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)