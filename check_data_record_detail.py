#!/usr/bin/env python3
"""
データ記録シートの詳細確認スクリプト
ヘッダーの重複問題を詳しく調査
"""
import sys
import os
sys.path.append('/workspace/shared')

import gspread
from google.oauth2.service_account import Credentials
from sheets_config import SCOPES

def check_data_record_detail():
    """データ記録シートの詳細確認"""
    
    credentials_file = '/workspace/web-app/backend/my-service-account.json'
    spreadsheet_id = '1OzUHxgBoFz6tzkd3hg4j3L2yeQ5Qw0vk3mIk4j4IjIM'
    
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print("🔍 === データ記録シート詳細確認 ===\n")
        
        sheet = spreadsheet.worksheet("データ記録")
        
        # 生データの最初の5行を取得
        raw_data = sheet.get_all_values()
        
        print(f"総行数: {len(raw_data)}")
        print(f"総列数: {len(raw_data[0]) if raw_data else 0}")
        
        print("\n📋 最初の5行の生データ:")
        for i, row in enumerate(raw_data[:5]):
            print(f"  行{i+1}: {row}")
        
        print(f"\n📋 ヘッダー行（1行目）の詳細:")
        if raw_data:
            headers = raw_data[0]
            for i, header in enumerate(headers):
                print(f"  列{i+1}: '{header}'")
        
        # データがある行数を確認
        data_rows = [row for row in raw_data[1:] if any(cell.strip() for cell in row)]
        print(f"\n📊 実際のデータ行数: {len(data_rows)}")
        
        if data_rows:
            print("\n📋 最初の3件のデータ:")
            for i, row in enumerate(data_rows[:3]):
                print(f"  データ{i+1}: {row}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_data_record_detail()