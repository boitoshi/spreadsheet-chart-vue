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
        
        # デフォルト銘柄テンプレート（外貨情報含む）
        from settings import DEFAULT_STOCKS
        self.default_stocks = DEFAULT_STOCKS
    
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
            
            # ヘッダー設定（現地通貨・為替レート情報を追加）
            headers = [
                "銘柄コード", "銘柄名", "取得日", "取得単価",
                "取得通貨", "取得時レート", "取得単価（円）",
                "保有株数", "外国株フラグ", "最終更新", "備考"
            ]
            portfolio_sheet.update('A1:K1', [headers])
            
            # スタイル設定（ヘッダー）
            portfolio_sheet.format('A1:K1', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })

            # デフォルトデータ投入（現地通貨・為替レート情報含む）
            row = 2
            for symbol, info in self.default_stocks.items():
                currency = info.get('currency', 'JPY')
                fx_rate = info.get('purchase_fx_rate', '')
                price_jpy = info['purchase_price'] * fx_rate if fx_rate else info['purchase_price']
                portfolio_sheet.update(f'A{row}:K{row}', [[
                    symbol,
                    info['name'],
                    info['purchase_date'],
                    info['purchase_price'],          # 現地通貨での取得単価
                    currency,                         # 取得通貨
                    fx_rate,                          # 取得時レート（JPYは空欄）
                    round(price_jpy, 2),              # 取得単価（円）
                    info['shares'],
                    '○' if info.get('is_foreign', False) else '×',
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
            
            # 市場データ専用ヘッダー（現地通貨価格・為替レート情報を追加）
            headers = [
                "月末日付", "銘柄コード", "現地通貨価格", "通貨", "為替レート",
                "月末価格（円）", "最高値", "最安値",
                "平均価格", "月間変動率(%)", "平均出来高", "取得日時"
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
            
            # ヘッダー設定（為替分離用列を追加）
            headers = [
                "日付", "銘柄コード", "銘柄名", "取得単価", "月末価格",
                "保有株数", "取得額", "評価額", "損益", "損益率(%)",
                "通貨", "現地通貨損益", "為替影響額", "更新日時"
            ]
            perf_sheet.update('A1:N1', [headers])
            
            # スタイル設定
            perf_sheet.format('A1:N1', {
                'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
                'textFormat': {'bold': True}
            })
            
            print("✅ 損益レポートシートの初期設定完了")
            return perf_sheet
            
        except Exception as e:
            print(f"損益レポートシート設定エラー: {e}")
            return None
    
    def setup_currency_sheet(self):
        """為替レートシートを初期設定"""
        try:
            try:
                currency_sheet = self.spreadsheet.worksheet("為替レート")
                print("✅ 為替レートシートは既に存在します")
                return currency_sheet
            except gspread.WorksheetNotFound:
                currency_sheet = self.spreadsheet.add_worksheet("為替レート", 500, 8)
                print("💱 新しい為替レートシートを作成しました")
            
            # ヘッダー設定
            headers = [
                "取得日", "通貨ペア", "レート", "前回レート", "変動率(%)", 
                "最高値", "最安値", "更新日時"
            ]
            currency_sheet.update('A1:H1', [headers])
            
            # スタイル設定
            currency_sheet.format('A1:H1', {
                'backgroundColor': {'red': 0.7, 'green': 0.7, 'blue': 0.9},
                'textFormat': {'bold': True}
            })
            
            print("✅ 為替レートシートの初期設定完了")
            return currency_sheet
            
        except Exception as e:
            print(f"為替レートシート設定エラー: {e}")
            return None
    
    def save_currency_rates(self, exchange_rates, date):
        """為替レートをスプレッドシートに保存"""
        try:
            currency_sheet = self.spreadsheet.worksheet("為替レート")
            
            # 既存データ取得（重複チェック用）
            existing_records = currency_sheet.get_all_records()
            
            new_count = 0
            updated_count = 0
            
            for currency, rate in exchange_rates.items():
                if currency == 'JPY':
                    continue
                
                date_str = date.strftime('%Y-%m-%d')
                currency_pair = f"{currency}/JPY"
                
                currency_data = [
                    date_str,
                    currency_pair,
                    round(rate, 2),
                    "",  # 前回レート（今後実装）
                    "",  # 変動率（今後実装）
                    "",  # 最高値（今後実装）
                    "",  # 最安値（今後実装）
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                
                # 既存データから同じ日付・通貨ペアを検索
                existing_row = self._find_existing_currency_row(existing_records, date_str, currency_pair)
                
                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    currency_sheet.update(f'A{row_number}:H{row_number}', [currency_data])
                    updated_count += 1
                    print(f"  🔄 更新: {currency_pair} ({date_str})")
                else:
                    # 新規データを追加
                    currency_sheet.append_row(currency_data)
                    new_count += 1
                    print(f"  ➕ 新規: {currency_pair} ({date_str})")
            
            print(f"✅ 為替レート保存完了: 新規{new_count}件、更新{updated_count}件")
            
        except Exception as e:
            print(f"為替レート保存エラー: {e}")
    
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
        """データ記録をスプレッドシートに保存（市場データ専用）"""
        try:
            data_sheet = self.spreadsheet.worksheet("データ記録")
            
            # 既存データ取得（重複チェック用）
            existing_records = data_sheet.get_all_records()
            
            new_count = 0
            updated_count = 0
            
            for data in data_record_results:
                date_str = data[0]  # 月末日付
                symbol = data[1]    # 銘柄コード
                
                # 既存データから同じ日付・銘柄を検索
                existing_row = self._find_existing_row(existing_records, date_str, symbol, 'データ記録')
                
                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    data_sheet.update(f'A{row_number}:L{row_number}', [data])
                    updated_count += 1
                    print(f"  🔄 更新: {symbol} ({date_str})")
                else:
                    # 新規データを追加
                    data_sheet.append_row(data)
                    new_count += 1
                    print(f"  ➕ 新規: {symbol} ({date_str})")
            
            print(f"✅ データ記録保存完了: 新規{new_count}件、更新{updated_count}件")
            
        except Exception as e:
            print(f"データ記録保存エラー: {e}")
    
    def save_performance_data(self, performance_results):
        """損益データをスプレッドシートに保存"""
        try:
            perf_sheet = self.spreadsheet.worksheet("損益レポート")
            
            # 既存データ取得（重複チェック用）
            existing_records = perf_sheet.get_all_records()
            
            new_count = 0
            updated_count = 0
            
            for data in performance_results:
                date_str = data[0]  # 日付
                symbol = data[1]    # 銘柄コード
                
                # 既存データから同じ日付・銘柄を検索
                existing_row = self._find_existing_row(existing_records, date_str, symbol, '損益レポート')
                
                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    perf_sheet.update(f'A{row_number}:N{row_number}', [data])
                    updated_count += 1
                    print(f"  🔄 更新: {data[2]} ({date_str})")  # 銘柄名を表示
                else:
                    # 新規データを追加
                    perf_sheet.append_row(data)
                    new_count += 1
                    print(f"  ➕ 新規: {data[2]} ({date_str})")  # 銘柄名を表示
            
            print(f"✅ 損益レポート保存完了: 新規{new_count}件、更新{updated_count}件")
            
        except Exception as e:
            print(f"損益レポート保存エラー: {e}")
    
    def display_portfolio_summary(self, year, month):
        """ポートフォリオサマリーを表示（重複除去）"""
        try:
            perf_sheet = self.spreadsheet.worksheet("損益レポート")
            records = perf_sheet.get_all_records()
            
            # 指定月のデータをフィルタリング（YYYY-MM-DD形式）
            target_prefix = f"{year}-{month:02d}-"
            current_data = [r for r in records if str(r['日付']).startswith(target_prefix)]
            
            if not current_data:
                print(f"⚠️ {year}年{month}月のデータが見つかりません")
                return
            
            # 重複除去：同じ銘柄コードが複数ある場合、最新の更新日時のもののみ残す
            unique_data = self._remove_duplicate_summary_records(current_data)
            
            print(f"\n📋 === {year}年{month}月 ポートフォリオサマリー ===")
            
            total_cost = sum(r['取得額'] for r in unique_data)
            total_value = sum(r['評価額'] for r in unique_data)
            total_pl = total_value - total_cost
            total_pl_rate = (total_pl / total_cost) * 100
            
            print(f"💰 合計取得額: {total_cost:,.0f}円")
            print(f"📈 合計評価額: {total_value:,.0f}円")
            print(f"{'🎉' if total_pl >= 0 else '😢'} 総合損益: {total_pl:+,.0f}円 ({total_pl_rate:+.1f}%)")
            
            print("\n📊 銘柄別詳細:")
            for data in unique_data:
                pl_emoji = "🎉" if data['損益'] >= 0 else "😢"
                print(f"  {pl_emoji} {data['銘柄名']}: {data['損益']:+,.0f}円 ({data['損益率(%)']:+.1f}%)")
            
        except Exception as e:
            print(f"サマリー表示エラー: {e}")
    
    def _remove_duplicate_summary_records(self, records):
        """サマリー表示用の重複除去"""
        stock_records = {}
        
        for record in records:
            stock_code = record.get('銘柄コード', '')
            if not stock_code:
                continue
            
            # 更新日時を取得（文字列として比較）
            update_time = record.get('更新日時', '')
            
            # 既存レコードがないか、より新しい更新日時の場合に更新
            if (stock_code not in stock_records or 
                update_time > stock_records[stock_code].get('更新日時', '')):
                stock_records[stock_code] = record
        
        return list(stock_records.values())
    
    def _find_existing_row(self, existing_records, date_str, symbol, sheet_type):
        """既存データから同じ日付・銘柄の行を検索
        
        Args:
            existing_records (list): 既存データレコード
            date_str (str): 検索する日付文字列
            symbol (str): 検索する銘柄コード
            sheet_type (str): シート種別（'データ記録' or '損益レポート'）
            
        Returns:
            dict: 見つかった行情報（row_number含む）またはNone
        """
        for i, record in enumerate(existing_records):
            # データ記録シートの場合
            if sheet_type == 'データ記録':
                if (record.get('月末日付') == date_str and 
                    record.get('銘柄コード') == symbol):
                    return {'row_number': i + 2, 'record': record}  # +2はヘッダー行を考慮
            
            # 損益レポートシートの場合
            elif sheet_type == '損益レポート':
                if (record.get('日付') == date_str and 
                    record.get('銘柄コード') == symbol):
                    return {'row_number': i + 2, 'record': record}  # +2はヘッダー行を考慮
        
        return None
    
    def _find_existing_currency_row(self, existing_records, date_str, currency_pair):
        """既存為替データから同じ日付・通貨ペアの行を検索
        
        Args:
            existing_records (list): 既存データレコード
            date_str (str): 検索する日付文字列
            currency_pair (str): 検索する通貨ペア
            
        Returns:
            dict: 見つかった行情報（row_number含む）またはNone
        """
        for i, record in enumerate(existing_records):
            if (record.get('取得日') == date_str and 
                record.get('通貨ペア') == currency_pair):
                return {'row_number': i + 2, 'record': record}  # +2はヘッダー行を考慮
        
        return None