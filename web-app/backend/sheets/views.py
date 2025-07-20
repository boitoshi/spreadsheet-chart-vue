import datetime
from django.http import JsonResponse
from django.shortcuts import render
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from django.conf import settings
from pathlib import Path

def calculate_profit_or_loss(purchase_price, current_price, quantity=1):
    try:
        return (float(current_price) - float(purchase_price)) * int(quantity)
    except:
        return 0.0

def format_row_to_object(row, headers_index):
    # 保有株数の処理（-1の場合はデフォルト値1を使用）
    quantity = 1 if headers_index['quantity_idx'] == -1 else row[headers_index['quantity_idx']]
    
    return {
        "label": row[headers_index['date_idx']],      # 月末日付
        "stock": row[headers_index['stock_idx']],     # 銘柄コード
        "value": row[headers_index['price_idx']],     # 月末価格
        "purchase": row[headers_index['purchase_idx']], # 平均価格
        "quantity": quantity,                         # 保有株数（デフォルト1）
        "pl_value": calculate_profit_or_loss(         # 損益
            row[headers_index['purchase_idx']], 
            row[headers_index['price_idx']], 
            quantity
        )
    }
    
def filter_and_calculate(data_rows, start_month, end_month, stock_symbol, headers_index):
    filtered_data = []
    for row in data_rows:
        if len(row) <= max(headers_index.values()):
            continue
        
        try:
            row_date = datetime.datetime.strptime(row[headers_index['date_idx']], '%Y-%m-%d')
        except ValueError:
            continue
        
        if not (start_month <= row_date <= end_month):
            continue
        
        if stock_symbol and row[headers_index['stock_idx']] != stock_symbol:
            continue
            
        filtered_data.append(format_row_to_object(row, headers_index))
    
    return filtered_data

def get_data(request):
    try:
        # クエリパラメータを取得
        start_month_str = request.GET.get('start_month', '2023-01')
        end_month_str = request.GET.get('end_month', '2024-12')
        stock_symbol = request.GET.get('stock', None)

        # start_month と end_month の変換
        try:
            start_month = datetime.datetime.strptime(start_month_str, '%Y-%m')
            end_month = datetime.datetime.strptime(end_month_str, '%Y-%m')
        except ValueError:
            return JsonResponse(
                {"error": "Invalid date format. Use YYYY-MM."}, 
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        # 環境変数から直接取得（settingsを経由）
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        spreadsheet_id = settings.SPREADSHEET_ID

        if not credentials_path or not Path(credentials_path).exists():
            return JsonResponse(
                {"error": f"Service account file not found at {credentials_path}"}, 
                status=404,
                json_dumps_params={'ensure_ascii': False}
            )
        
        # 認証情報の設定
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )

        # スプレッドシートAPIを利用するためのクライアント作成
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # スプレッドシートのIDと範囲を指定してデータを取得
        RANGE_NAME = "データ記録!A1:L" # 列を追加するときはLを変更
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])

        if not values:
            return JsonResponse(
                {"message": "No data found."},
                json_dumps_params={'ensure_ascii': False}
            )
        
        # 最初の行をヘッダーとして使用
        headers = values[0]
        data_rows = values[1:]

        # デバッグ用：ヘッダー情報を返す
        if 'debug' in request.GET:
            return JsonResponse(
                {"headers": headers, "total_columns": len(headers)}, 
                json_dumps_params={'ensure_ascii': False}
            )

        # ヘッダーの列名を指定（柔軟に対応）
        try:
            # 列名のバリエーションに対応
            date_idx = None
            stock_idx = None
            purchase_idx = None
            quantity_idx = None
            price_idx = None
            
            for i, header in enumerate(headers):
                if '月末日付' in header or '日付' in header:
                    date_idx = i
                elif '銘柄コード' in header or '銘柄' in header or '株式' in header or '名前' in header:
                    stock_idx = i
                elif '平均価格' in header or '取得価格' in header or '購入価格' in header:
                    purchase_idx = i
                elif '保有株数' in header or '株数' in header:
                    quantity_idx = i  # スプレッドシートにない場合はデフォルト値使用
                elif '月末価格' in header or '現在価格' in header or '報告月末価格' in header:
                    price_idx = i
            
            # 必須カラムのチェック（保有株数はオプション）
            missing_columns = []
            if date_idx is None:
                missing_columns.append('日付関連')
            if stock_idx is None:
                missing_columns.append('銘柄関連')
            if purchase_idx is None:
                missing_columns.append('取得価格関連')
            if price_idx is None:
                missing_columns.append('現在価格関連')
            
            # 保有株数がない場合はデフォルト値（1株）を使用
            if quantity_idx is None:
                quantity_idx = -1  # -1は特別値としてデフォルト株数を示す
                
            if missing_columns:
                return JsonResponse(
                    {
                        "error": f"Required columns not found: {', '.join(missing_columns)}", 
                        "available_headers": headers,
                        "hint": "Use ?debug=1 to see all available headers"
                    }, 
                    status=400,
                    json_dumps_params={'ensure_ascii': False}
                )
                
        except Exception as e:
            return JsonResponse(
                {"error": f"Header processing error: {str(e)}", "headers": headers}, 
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )
        
        headers_index = {
            'date_idx': date_idx,
            'stock_idx': stock_idx,
            'purchase_idx': purchase_idx,
            'price_idx': price_idx,
            'quantity_idx': quantity_idx
        }


        
        # フィルタリング
        filtered_data = filter_and_calculate(
            data_rows,
            start_month,
            end_month,
            stock_symbol,
            headers_index     # ← これだけでOK！
        )

        return JsonResponse(
            {"data": filtered_data},
            json_dumps_params={'ensure_ascii': False}
        )
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500,
            json_dumps_params={'ensure_ascii': False}
        )

def api_index(request):
    """APIエンドポイント一覧表示"""
    api_endpoints = [
        {
            'path': '/admin/',
            'method': 'GET', 
            'description': 'Django管理画面',
            'category': '管理'
        },
        {
            'path': '/get_data/',
            'method': 'GET',
            'description': 'Google Sheetsからポートフォリオデータを取得',
            'parameters': 'start_month, end_month, stock_symbol',
            'category': 'データ取得'
        },
        {
            'path': '/api/manual_update/',
            'method': 'POST',
            'description': '手動での株価更新',
            'category': 'データ更新'
        },
        {
            'path': '/api/portfolio/',
            'method': 'GET',
            'description': 'ポートフォリオデータAPI（Vue.js用）',
            'category': 'フロントエンド連携'
        },
        {
            'path': '/api/portfolio/history/',
            'method': 'GET',
            'description': '損益推移履歴API',
            'category': 'フロントエンド連携'
        },
        {
            'path': '/portfolio/',
            'method': 'GET',
            'description': 'ポートフォリオデータ（外貨対応）',
            'category': 'データ取得'
        },
        {
            'path': '/currency_rates/',
            'method': 'GET',
            'description': '為替レート情報',
            'category': 'データ取得'
        },
        {
            'path': '/generate_report/<month>/',
            'method': 'GET',
            'description': '月次レポート生成',
            'parameters': 'month (YYYY-MM形式)',
            'category': 'レポート'
        }
    ]
    
    context = {
        'api_endpoints': api_endpoints,
        'project_name': '投資ポートフォリオ管理API',
        'description': 'Vue.js + Django による投資ポートフォリオ管理システムのバックエンドAPI'
    }
    
    return render(request, 'api_index.html', context)
