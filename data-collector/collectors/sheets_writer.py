import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import sys
import os

# 共通設定をインポートするためのパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from sheets_config import SCOPES


class SheetsDataWriter:
    """Google Sheetsへのデータ書き込みクラス"""
    
    def __init__(self, credentials_file, spreadsheet_id):
        """初期化
        
        Args:
            credentials_file (str): サービスアカウントのJSONファイルパス
            spreadsheet_id (str): スプレッドシートのID
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.gc = None
        self.spreadsheet = None
        
        # デフォルト銘柄テンプレート
        self.default_stocks = {
            "7974.T": {"name": "任天堂", "purchase_price": 5500, "shares": 10, "purchase_date": "2024-01-15"},
            "2432.T": {"name": "DeNA", "purchase_price": 2100, "shares": 5, "purchase_date": "2024-02-10"},
            "NVDA": {"name": "エヌビディア", "purchase_price": 850, "shares": 2, "purchase_date": "2024-03-05"}
        }
    
    def setup_google_sheets(self):
        """Google Sheetsの認証設定"""
        try:
            if not self.credentials_file:
                print("⚠️ Google Sheets APIの認証ファイルが設定されていません。")
                return False
                
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self.gc = gspread.authorize(creds)
            
            if self.spreadsheet_id:
                self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            else:
                self.spreadsheet = self.gc.create("ポートフォリオ管理システム")
                print(f"新しいスプレッドシートを作成しました: {self.spreadsheet.url}")
                
            return True
            
        except Exception as e:
            print(f"Google Sheets設定エラー: {e}")
            return False
    
    def setup_portfolio_sheet(self):
        """ポートフォリオマスタシートを初期設定"""
        try:
            # 既存シートをチェック
            try:
                portfolio_sheet = self.spreadsheet.worksheet("ポートフォリオ")
                print("✅ ポートフォリオシートは既に存在します")
                return portfolio_sheet
            except gspread.WorksheetNotFound:
                # 新しいシート作成
                portfolio_sheet = self.spreadsheet.add_worksheet("ポートフォリオ", 100, 10)
                print("📋 新しいポートフォリオシートを作成しました")
            
            # ヘッダー設定
            headers = [
                "銘柄コード", "銘柄名", "取得日", "取得単価（円）", 
                "保有株数", "取得額合計", "最終更新", "備考"
            ]
            portfolio_sheet.update('A1:H1', [headers])
            
            # スタイル設定（ヘッダー）
            portfolio_sheet.format('A1:H1', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })
            
            # デフォルトデータ投入
            row = 2
            for symbol, info in self.default_stocks.items():
                portfolio_sheet.update(f'A{row}:H{row}', [[
                    symbol,
                    info['name'],
                    info['purchase_date'],
                    info['purchase_price'],
                    info['shares'],
                    f"=D{row}*E{row}",  # 取得額合計（自動計算）
                    datetime.now().strftime('%Y-%m-%d'),
                    "デフォルト設定"
                ]])
                row += 1
            
            print("✅ ポートフォリオマスタの初期設定完了")
            return portfolio_sheet
            
        except Exception as e:
            print(f"ポートフォリオシート設定エラー: {e}")
            return None
    
    def setup_data_record_sheet(self):
        """データ記録シートを初期設定（Django backend仕様に合わせる）"""
        try:
            try:
                data_sheet = self.spreadsheet.worksheet("データ記録")
                print("✅ データ記録シートは既に存在します")
                return data_sheet
            except gspread.WorksheetNotFound:
                data_sheet = self.spreadsheet.add_worksheet("データ記録", 1000, 15)
                print("📈 新しいデータ記録シートを作成しました")
            
            # Django backendが期待するヘッダー名を使用
            headers = [
                "月末日付", "銘柄", "取得価格（円）", "報告月末価格（円）", "保有株数",
                "最高値", "最安値", "平均価格", "月間変動率(%)", "平均出来高", "取得日時", "備考"
            ]
            data_sheet.update('A1:L1', [headers])
            
            # スタイル設定
            data_sheet.format('A1:L1', {
                'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
                'textFormat': {'bold': True}
            })
            
            print("✅ データ記録シートの初期設定完了")
            return data_sheet
            
        except Exception as e:
            print(f"データ記録シート設定エラー: {e}")
            return None
    
    def setup_performance_sheet(self):
        """パフォーマンス計算シートを初期設定"""
        try:
            try:
                perf_sheet = self.spreadsheet.worksheet("損益レポート")
                print("✅ 損益レポートシートは既に存在します")
                return perf_sheet
            except gspread.WorksheetNotFound:
                perf_sheet = self.spreadsheet.add_worksheet("損益レポート", 1000, 12)
                print("📊 新しい損益レポートシートを作成しました")
            
            # ヘッダー設定
            headers = [
                "日付", "銘柄コード", "銘柄名", "取得単価", "月末価格", 
                "保有株数", "取得額", "評価額", "損益", "損益率(%)", "更新日時"
            ]
            perf_sheet.update('A1:K1', [headers])
            
            # スタイル設定
            perf_sheet.format('A1:K1', {
                'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
                'textFormat': {'bold': True}
            })
            
            print("✅ 損益レポートシートの初期設定完了")
            return perf_sheet
            
        except Exception as e:
            print(f"損益レポートシート設定エラー: {e}")
            return None
    
    def get_portfolio_data(self):
        """ポートフォリオデータを取得"""
        try:
            portfolio_sheet = self.spreadsheet.worksheet("ポートフォリオ")
            records = portfolio_sheet.get_all_records()
            return records
        except Exception as e:
            print(f"ポートフォリオデータ取得エラー: {e}")
            return []
    
    def save_data_record(self, data_record_results):
        """データ記録をスプレッドシートに保存（Django backend用）"""
        try:
            data_sheet = self.spreadsheet.worksheet("データ記録")
            
            # データを追加
            for data in data_record_results:
                data_sheet.append_row(data)
            
            print(f"✅ データ記録 {len(data_record_results)}件を保存しました（Django backend対応）")
            
        except Exception as e:
            print(f"データ記録保存エラー: {e}")
    
    def save_performance_data(self, performance_results):
        """損益データをスプレッドシートに保存"""
        try:
            perf_sheet = self.spreadsheet.worksheet("損益レポート")
            
            # データを追加
            for data in performance_results:
                perf_sheet.append_row(data)
            
            print(f"✅ 損益レポート {len(performance_results)}件を保存しました")
            
        except Exception as e:
            print(f"損益レポート保存エラー: {e}")
    
    def display_portfolio_summary(self, year, month):
        """ポートフォリオサマリーを表示"""
        try:
            perf_sheet = self.spreadsheet.worksheet("損益レポート")
            records = perf_sheet.get_all_records()
            
            # 指定月のデータをフィルタリング
            target_date = f"{year}-{month:02d}-末"
            current_data = [r for r in records if r['日付'] == target_date]
            
            if not current_data:
                print(f"⚠️ {year}年{month}月のデータが見つかりません")
                return
            
            print(f"\n📋 === {year}年{month}月 ポートフォリオサマリー ===")
            
            total_cost = sum(r['取得額'] for r in current_data)
            total_value = sum(r['評価額'] for r in current_data)
            total_pl = total_value - total_cost
            total_pl_rate = (total_pl / total_cost) * 100
            
            print(f"💰 合計取得額: {total_cost:,.0f}円")
            print(f"📈 合計評価額: {total_value:,.0f}円")
            print(f"{'🎉' if total_pl >= 0 else '😢'} 総合損益: {total_pl:+,.0f}円 ({total_pl_rate:+.1f}%)")
            
            print("\n📊 銘柄別詳細:")
            for data in current_data:
                pl_emoji = "🎉" if data['損益'] >= 0 else "😢"
                print(f"  {pl_emoji} {data['銘柄名']}: {data['損益']:+,.0f}円 ({data['損益率(%)']:+.1f}%)")
            
        except Exception as e:
            print(f"サマリー表示エラー: {e}")