import datetime
from django.http import JsonResponse
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
    return {
        "label": row[headers_index['date_idx']],      # 月末日付
        "stock": row[headers_index['stock_idx']],     # 銘柄
        "value": row[headers_index['price_idx']],     # 報告月末価格
        "purchase": row[headers_index['purchase_idx']], # 取得価格
        "quantity": row[headers_index['quantity_idx']], # 保有株数
        "pl_value": calculate_profit_or_loss(         # 損益
            row[headers_index['purchase_idx']], 
            row[headers_index['price_idx']], 
            row[headers_index['quantity_idx']]
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

        # ヘッダーの列名を指定
        try:
            date_idx            = headers.index('月末日付') 
            stock_idx           = headers.index('銘柄')
            purchase_idx        = headers.index('取得価格（円）')  # 取得価格
            # purchase_date_idx   = headers.index('取得日付') # 取得日付
            quantity_idx        = headers.index('保有株数')     # 保有株数があれば
            price_idx           = headers.index('報告月末価格（円）')   
        except ValueError as e:
            return JsonResponse(
                {"error": f"Required column not found: {str(e)}"}, 
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
