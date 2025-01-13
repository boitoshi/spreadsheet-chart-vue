from django.http import JsonResponse
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from django.conf import settings
import os
from pathlib import Path

def get_data(request):
    try:
        # 環境変数から直接取得（settingsを経由）
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        spreadsheet_id = settings.SPREADSHEET_ID

        if not credentials_path or not Path(credentials_path).exists():
            return JsonResponse(
                {"error": f"Service account file not found at {credentials_path}"}, 
                status=404
            )
        
        # 認証情報の設定
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )

        # スプレッドシートAPIを利用するためのクライアント作成
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # スプレッドシートのIDと範囲を指定
        SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
        RANGE_NAME = "データ記録!A1:J39"

        # スプレッドシートからデータを取得
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            return JsonResponse({"message": "No data found."})
        else:
            return JsonResponse({"data": values})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
