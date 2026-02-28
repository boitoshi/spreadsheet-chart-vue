#!/usr/bin/env python3
"""
Google Sheets API権限テストスクリプト
"""

import os
import sys

sys.path.append('collectors')
sys.path.append('config')

from settings import GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID
from sheets_writer import SheetsDataWriter


def test_google_sheets_permissions() -> bool | None:
    """Google Sheets権限テスト"""
    print("=== Google Sheets API権限テスト ===")
    print(f"📋 スプレッドシートID: {SPREADSHEET_ID}")
    print(f"🔑 認証ファイル: {GOOGLE_APPLICATION_CREDENTIALS}")

    # 認証ファイル存在確認
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        print(f"❌ 認証ファイルが見つかりません: {GOOGLE_APPLICATION_CREDENTIALS}")
        return False

    print("✅ 認証ファイル存在確認")

    # Google Sheets接続テスト
    writer = SheetsDataWriter(GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID)

    print("\n📡 Google Sheets接続テスト...")
    if not writer.setup_google_sheets():
        print("❌ Google Sheets接続失敗")
        return False

    print("✅ Google Sheets接続成功")

    # スプレッドシート情報取得
    try:
        print("\n📊 スプレッドシート情報取得...")
        spreadsheet_info = writer.spreadsheet
        print(f"✅ スプレッドシート名: {spreadsheet_info.title}")
        print(f"✅ URL: {spreadsheet_info.url}")

        # 既存シート一覧取得
        worksheets = spreadsheet_info.worksheets()
        print(f"✅ 既存シート数: {len(worksheets)}")
        for ws in worksheets:
            print(f"   - {ws.title}")

    except Exception as e:
        print(f"❌ スプレッドシート情報取得エラー: {e}")
        return False

    # 読み取り権限テスト
    try:
        print("\n📖 読み取り権限テスト...")
        portfolio_data = writer.get_portfolio_data()
        print(f"✅ ポートフォリオデータ取得成功: {len(portfolio_data)}件")

    except Exception as e:
        print(f"❌ 読み取り権限エラー: {e}")
        return False

    # 書き込み権限テスト
    try:
        print("\n✏️ 書き込み権限テスト...")

        # テスト用シートを作成
        test_sheet_name = "権限テスト"
        try:
            test_sheet = spreadsheet_info.worksheet(test_sheet_name)
            print(f"✅ テストシート「{test_sheet_name}」は既に存在します")
        except Exception:
            test_sheet = spreadsheet_info.add_worksheet(test_sheet_name, 5, 5)
            print(f"✅ テストシート「{test_sheet_name}」を作成しました")

        # テストデータ書き込み
        from datetime import datetime
        test_data = [["テスト", "データ", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]
        test_sheet.update('A1:C1', test_data)
        print("✅ テストデータ書き込み成功")

        # テストシート削除
        spreadsheet_info.del_worksheet(test_sheet)
        print("✅ テストシート削除成功")

    except Exception as e:
        print(f"❌ 書き込み権限エラー: {e}")
        print(
            "   → サービスアカウントを「編集者」権限で"
            "スプレッドシートに追加してください"
        )
        return False

    print("\n🎉 すべての権限テストが成功しました！")
    print("   データ収集システムが正常に動作可能です。")
    return True

if __name__ == "__main__":
    success = test_google_sheets_permissions()
    if not success:
        print("\n🔧 解決方法:")
        print("1. スプレッドシートの共有設定を確認")
        print("2. サービスアカウントを「編集者」権限で追加:")
        print("   spreadsheet-access@pokebros-project.iam.gserviceaccount.com")
        print("3. Google Cloud ConsoleでAPI有効化確認")
        print("4. docs/google-sheets-setup.md を参照")
        sys.exit(1)
    else:
        sys.exit(0)
