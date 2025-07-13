#!/usr/bin/env python3
"""
Google Sheetsの現在のデータ状況を確認するスクリプト
data-collector修正前の現状把握用
"""
import sys
import os
sys.path.append('/workspace/shared')

import gspread
from google.oauth2.service_account import Credentials
from sheets_config import SCOPES, SHEET_NAMES

def check_sheets_data():
    """Google Sheetsの各シートのデータ状況を確認"""
    
    # 認証設定
    credentials_file = '/workspace/web-app/backend/my-service-account.json'
    spreadsheet_id = '1OzUHxgBoFz6tzkd3hg4j3L2yeQ5Qw0vk3mIk4j4IjIM'
    
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print("🔍 === Google Sheets データ状況確認 ===\n")
        
        # 各シートの確認
        for sheet_key, sheet_name in SHEET_NAMES.items():
            print(f"📋 【{sheet_name}】シート:")
            
            try:
                sheet = spreadsheet.worksheet(sheet_name)
                records = sheet.get_all_records()
                
                print(f"  データ件数: {len(records)}件")
                
                if records:
                    # ヘッダー確認
                    headers = list(records[0].keys())
                    print(f"  ヘッダー: {', '.join(headers)}")
                    
                    # 最初の3件のサンプル表示
                    print(f"  サンプルデータ（最大3件）:")
                    for i, record in enumerate(records[:3]):
                        print(f"    [{i+1}] {record}")
                    
                    if len(records) > 3:
                        print(f"    ... (他 {len(records)-3}件)")
                else:
                    print("  データなし")
                    
            except gspread.WorksheetNotFound:
                print(f"  ⚠️ シートが見つかりません")
            except Exception as e:
                print(f"  ❌ エラー: {e}")
            
            print()
        
    except Exception as e:
        print(f"❌ Google Sheets接続エラー: {e}")

if __name__ == "__main__":
    check_sheets_data()