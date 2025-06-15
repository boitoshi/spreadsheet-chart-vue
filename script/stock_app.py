import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

# Google Sheets API設定
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class PortfolioStockApp:
    def __init__(self, credentials_file=None, spreadsheet_id=None):
        """
        初期化
        
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

    def get_stock_data(self, symbol, year, month):
        """株価データを取得"""
        try:
            # 月の開始日と終了日を計算
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # yfinanceでデータ取得
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date + timedelta(days=1))
            
            if data.empty:
                print(f"⚠️ {symbol} のデータが取得できませんでした")
                return None
            
            return data
        
        except Exception as e:
            print(f"株価データ取得エラー ({symbol}): {e}")
            return None

    def calculate_portfolio_performance(self, year, month):
        """ポートフォリオパフォーマンス計算"""
        print(f"\n📊 {year}年{month}月のポートフォリオ分析を開始...")
        
        # ポートフォリオ情報取得
        portfolio_data = self.get_portfolio_data()
        if not portfolio_data:
            print("❌ ポートフォリオデータが取得できませんでした")
            return []
        
        results = []
        data_record_results = []
        
        # 月末日付を計算
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        for holding in portfolio_data:
            symbol = holding['銘柄コード']
            name = holding['銘柄名']
            purchase_price = float(holding['取得単価（円）'])
            shares = int(holding['保有株数'])
            
            print(f"  📈 {name} ({symbol}) を処理中...")
            
            # 株価データ取得
            stock_data = self.get_stock_data(symbol, year, month)
            if stock_data is None:
                continue
            
            # 株価情報の計算
            month_start_price = stock_data['Close'].iloc[0]
            month_end_price = stock_data['Close'].iloc[-1]
            highest_price = stock_data['High'].max()
            lowest_price = stock_data['Low'].min()
            average_price = stock_data['Close'].mean()
            monthly_change = ((month_end_price / month_start_price) - 1) * 100
            average_volume = stock_data['Volume'].mean()
            
            # Django backendが期待するデータ記録形式に合わせる
            data_record_results.append([
                last_day.strftime('%Y-%m-%d'),  # 月末日付
                symbol,                         # 銘柄
                purchase_price,                 # 取得価格（円）
                round(month_end_price, 2),     # 報告月末価格（円）
                shares,                         # 保有株数
                round(highest_price, 2),        # 最高値
                round(lowest_price, 2),         # 最安値
                round(average_price, 2),        # 平均価格
                round(monthly_change, 2),       # 月間変動率(%)
                int(average_volume),            # 平均出来高
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 取得日時
                f"自動取得 ({name})"             # 備考
            ])
            
            # 損益計算
            purchase_amount = purchase_price * shares
            current_amount = month_end_price * shares
            profit_loss = current_amount - purchase_amount
            profit_rate = (profit_loss / purchase_amount) * 100
            
            # 損益レポート用データ準備
            results.append([
                f"{year}-{month:02d}-末",
                symbol,
                name,
                purchase_price,
                round(month_end_price, 2),
                shares,
                purchase_amount,
                round(current_amount, 2),
                round(profit_loss, 2),
                round(profit_rate, 2),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            
            print(f"    ✅ {name}: {profit_loss:+,.0f}円 ({profit_rate:+.1f}%)")
        
        # データをスプレッドシートに保存
        if data_record_results:
            self.save_data_record(data_record_results)
        
        if results:
            self.save_performance_data(results)
        
        return results

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

    def run(self):
        """メイン実行関数"""
        print("=== 📊 ポートフォリオ管理システム ===")
        print("🎯 Django backend連携対応版")
        
        # Google Sheets設定
        if not self.setup_google_sheets():
            print("❌ Google Sheets接続に失敗しました")
            return
        
        # 初期シート設定
        self.setup_portfolio_sheet()
        self.setup_data_record_sheet()  # Django backend用データ記録シート
        self.setup_performance_sheet()
        
        while True:
            try:
                print("\n=== メインメニュー ===")
                print("1. 月次データ取得・分析")
                print("2. ポートフォリオサマリー表示")
                print("3. ポートフォリオ一覧表示")
                print("4. シート初期化")
                print("0. 終了")
                
                choice = input("\n選択してください: ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    # 月次データ取得
                    year = int(input("年を入力してください (例: 2024): "))
                    month = int(input("月を入力してください (1-12): "))
                    
                    if month < 1 or month > 12:
                        print("月は1-12の範囲で入力してください。")
                        continue
                    
                    # データ取得・分析実行
                    results = self.calculate_portfolio_performance(year, month)
                    
                    if results:
                        print(f"\n🎉 {year}年{month}月のデータ取得・分析が完了しました！")
                        print("   Django backendからWebアプリで確認できます")
                        self.display_portfolio_summary(year, month)
                    else:
                        print("❌ データの取得に失敗しました")
                
                elif choice == '2':
                    # サマリー表示
                    year = int(input("表示する年を入力 (例: 2024): "))
                    month = int(input("表示する月を入力 (1-12): "))
                    self.display_portfolio_summary(year, month)
                
                elif choice == '3':
                    # ポートフォリオ一覧
                    portfolio_data = self.get_portfolio_data()
                    if portfolio_data:
                        print("\n📋 現在のポートフォリオ:")
                        for stock in portfolio_data:
                            print(f"  📈 {stock['銘柄名']} ({stock['銘柄コード']}): {stock['保有株数']}株 @{stock['取得単価（円）']}円")
                    else:
                        print("❌ ポートフォリオデータが取得できません")
                
                elif choice == '4':
                    # シート初期化
                    confirm = input("⚠️ 全シートを初期化しますか？ (yes/no): ")
                    if confirm.lower() == 'yes':
                        self.setup_portfolio_sheet()
                        self.setup_data_record_sheet()
                        self.setup_performance_sheet()
                        print("✅ シートの初期化が完了しました")
                
                else:
                    print("❌ 無効な選択です")
                    
            except ValueError:
                print("❌ 正しい数値を入力してください")
            except KeyboardInterrupt:
                print("\nアプリを終了します")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")

def main():
    """メイン関数"""
    # .envファイルから設定を読み込み
    load_dotenv()
    
    # 環境変数から設定を取得（backendと同じ設定を使用）
    CREDENTIALS_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'my-service-account.json')
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    
    if not SPREADSHEET_ID:
        print("❌ SPREADSHEET_IDが設定されていません。backend/.envファイルを確認してください。")
        print("   例: SPREADSHEET_ID=your_spreadsheet_id_here")
        return
    
    print(f"📋 スプレッドシートID: {SPREADSHEET_ID}")
    print(f"🔑 認証ファイル: {CREDENTIALS_FILE}")
    
    app = PortfolioStockApp(CREDENTIALS_FILE, SPREADSHEET_ID)
    app.run()

if __name__ == "__main__":
    main()