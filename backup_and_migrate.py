#!/usr/bin/env python3
"""
Google Sheetsデータ記録シートの安全な移行スクリプト
Phase 1: 既存シートのバックアップ
"""
import sys
import os
sys.path.append('/workspace/shared')

import gspread
from google.oauth2.service_account import Credentials
from sheets_config import SCOPES
from datetime import datetime

def backup_data_record_sheet():
    """既存のデータ記録シートをバックアップ"""
    
    credentials_file = '/workspace/web-app/backend/my-service-account.json'
    spreadsheet_id = '1OzUHxgBoFz6tzkd3hg4j3L2yeQ5Qw0vk3mIk4j4IjIM'
    
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print("🛡️ === データ記録シートバックアップ開始 ===\n")
        
        # 既存のデータ記録シートを取得
        original_sheet = spreadsheet.worksheet("データ記録")
        
        # バックアップ名を生成（タイムスタンプ付き）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"データ記録_旧_{timestamp}"
        
        print(f"📋 既存シート名: データ記録")
        print(f"📋 バックアップ先: {backup_name}")
        
        # 全データを取得
        all_data = original_sheet.get_all_values()
        print(f"📊 バックアップ対象データ: {len(all_data)}行 × {len(all_data[0]) if all_data else 0}列")
        
        # 新しいシートを作成してデータをコピー
        backup_sheet = spreadsheet.add_worksheet(
            title=backup_name,
            rows=len(all_data) + 10,  # 余裕を持たせる
            cols=max(len(row) for row in all_data) if all_data else 12
        )
        
        # データを一括コピー
        if all_data:
            backup_sheet.update(f'A1:{chr(ord("A") + len(all_data[0]) - 1)}{len(all_data)}', all_data)
        
        # スタイル設定（ヘッダー行）
        if all_data:
            backup_sheet.format('A1:L1', {
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.6},
                'textFormat': {'bold': True}
            })
        
        print(f"✅ バックアップ完了: {backup_name}")
        print(f"📊 コピーされたデータ: {len(all_data)}行")
        
        return backup_name, all_data
        
    except Exception as e:
        print(f"❌ バックアップエラー: {e}")
        return None, None

def create_new_data_record_sheet():
    """新しいデータ記録シートを作成"""
    
    credentials_file = '/workspace/web-app/backend/my-service-account.json'
    spreadsheet_id = '1OzUHxgBoFz6tzkd3hg4j3L2yeQ5Qw0vk3mIk4j4IjIM'
    
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        print("\n🆕 === 新データ記録シート作成 ===\n")
        
        # 既存の「データ記録」シートを削除
        try:
            old_sheet = spreadsheet.worksheet("データ記録")
            spreadsheet.del_worksheet(old_sheet)
            print("🗑️ 旧データ記録シートを削除しました")
        except gspread.WorksheetNotFound:
            print("⚠️ 削除対象のシートが見つかりません")
        
        # 新しいヘッダー構造（市場データのみ）
        new_headers = [
            "月末日付", "銘柄コード", "月末価格（円）", "最高値", "最安値", 
            "平均価格", "月間変動率(%)", "平均出来高", "取得日時"
        ]
        
        # 新しいシートを作成
        new_sheet = spreadsheet.add_worksheet(
            title="データ記録",
            rows=1000,  # 十分な行数
            cols=len(new_headers)
        )
        
        # ヘッダーを設定
        new_sheet.update('A1:I1', [new_headers])
        
        # スタイル設定
        new_sheet.format('A1:I1', {
            'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
            'textFormat': {'bold': True}
        })
        
        print(f"✅ 新データ記録シート作成完了")
        print(f"📋 新ヘッダー: {', '.join(new_headers)}")
        
        return new_sheet
        
    except Exception as e:
        print(f"❌ 新シート作成エラー: {e}")
        return None

if __name__ == "__main__":
    print("🚀 データ記録シート移行プロセス開始\n")
    
    # Phase 1: バックアップ
    backup_name, backup_data = backup_data_record_sheet()
    
    if backup_name:
        # Phase 2: 新シート作成
        new_sheet = create_new_data_record_sheet()
        
        if new_sheet:
            print(f"\n🎉 === 移行完了 ===")
            print(f"✅ バックアップ: {backup_name}")
            print(f"✅ 新シート: データ記録 (市場データ専用)")
            print(f"📊 バックアップされたデータ: {len(backup_data) if backup_data else 0}行")
            print(f"\n⚠️ 次のステップ: コード修正が必要です")
        else:
            print(f"\n❌ 新シート作成に失敗しました")
    else:
        print(f"\n❌ バックアップに失敗しました")