import os
from django.http import JsonResponse
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def get_spreadsheet_data(request):
    # サービスアカウントの認証情報を設定
    service_account_file = os.getenv('SERVICE_ACCOUNT_KEY_PATH')
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    
    credentials = Credentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    # スプレッドシートサービスを構築
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    # データを読み込む
    range_name = "Sheet1!A1:E10"  # 必要に応じて範囲を変更
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        return JsonResponse({"message": "データが見つかりませんでした！"}, status=404)

    # データをJSON形式で返す
    return JsonResponse({"data": values})
