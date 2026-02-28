import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# 共通設定をインポートするためのパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from sheets_config import COLUMN_RANGES, HEADERS, SCOPES, SHEET_NAMES


class SheetsDataWriter:
    """Google Sheetsへのデータ書き込みクラス"""

    def __init__(self, credentials_file: str, spreadsheet_id: str) -> None:
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

    def setup_google_sheets(self) -> bool:
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

    def setup_portfolio_sheet(self) -> gspread.Worksheet | None:
        """ポートフォリオマスタシートを初期設定"""
        try:
            # 既存シートをチェック
            try:
                portfolio_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PORTFOLIO'])
                print("✅ ポートフォリオシートは既に存在します")
                return portfolio_sheet
            except gspread.WorksheetNotFound:
                # 新しいシート作成（12カラム）
                portfolio_sheet = self.spreadsheet.add_worksheet(
                    SHEET_NAMES['PORTFOLIO'], 100, len(HEADERS['PORTFOLIO'])
                )
                print("📋 新しいポートフォリオシートを作成しました")

            # ヘッダー設定（共通定義から取得）
            headers = HEADERS['PORTFOLIO']
            col_range = COLUMN_RANGES['PORTFOLIO']
            portfolio_sheet.update(f'{col_range}1', [headers])

            # スタイル設定（ヘッダー）
            portfolio_sheet.format(f'{col_range}1', {
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                'textFormat': {'bold': True}
            })

            # デフォルトデータ投入（外貨情報含む）
            row = 2
            for symbol, info in self.default_stocks.items():
                portfolio_sheet.update(f'A{row}:L{row}', [[
                    symbol,
                    info['name'],
                    info['purchase_date'],
                    f"=E{row}*F{row}",  # 取得単価（円）= 外貨単価 × 為替レート
                    info.get('purchase_price_foreign', info['purchase_price']),
                    info.get('purchase_exchange_rate', 1.0),
                    info['shares'],
                    f"=D{row}*G{row}",  # 取得額合計 = 取得単価（円）× 保有株数
                    info.get('currency', 'JPY'),
                    '○' if info.get('is_foreign', False) else '×',
                    datetime.now().strftime('%Y-%m-%d'),
                    "デフォルト設定",
                ]])
                row += 1

            print("✅ ポートフォリオマスタの初期設定完了")
            return portfolio_sheet

        except Exception as e:
            print(f"ポートフォリオシート設定エラー: {e}")
            return None

    def setup_data_record_sheet(self) -> gspread.Worksheet | None:
        """データ記録シートを初期設定（Django backend仕様に合わせる）"""
        try:
            try:
                data_sheet = self.spreadsheet.worksheet("データ記録")
                print("✅ データ記録シートは既に存在します")
                return data_sheet
            except gspread.WorksheetNotFound:
                data_sheet = self.spreadsheet.add_worksheet("データ記録", 1000, 15)
                print("📈 新しいデータ記録シートを作成しました")

            # 市場データ専用ヘッダー（保有情報を除外）
            headers = [
                "月末日付", "銘柄コード", "月末価格（円）", "最高値", "最安値",
                "平均価格", "月間変動率(%)", "平均出来高", "取得日時"
            ]
            data_sheet.update('A1:I1', [headers])

            # スタイル設定
            data_sheet.format('A1:I1', {
                'backgroundColor': {'red': 0.7, 'green': 0.9, 'blue': 0.7},
                'textFormat': {'bold': True}
            })

            print("✅ データ記録シートの初期設定完了")
            return data_sheet

        except Exception as e:
            print(f"データ記録シート設定エラー: {e}")
            return None

    def setup_performance_sheet(self) -> gspread.Worksheet | None:
        """パフォーマンス計算シートを初期設定"""
        try:
            try:
                perf_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PERFORMANCE'])
                print("✅ 損益レポートシートは既に存在します")
                return perf_sheet
            except gspread.WorksheetNotFound:
                perf_sheet = self.spreadsheet.add_worksheet(
                    SHEET_NAMES['PERFORMANCE'], 1000, len(HEADERS['PERFORMANCE'])
                )
                print("📊 新しい損益レポートシートを作成しました")

            # ヘッダー設定（共通定義から取得）
            headers = HEADERS['PERFORMANCE']
            col_range = COLUMN_RANGES['PERFORMANCE']
            perf_sheet.update(f'{col_range}1', [headers])

            # スタイル設定
            perf_sheet.format(f'{col_range}1', {
                'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.7},
                'textFormat': {'bold': True}
            })

            print("✅ 損益レポートシートの初期設定完了")
            return perf_sheet

        except Exception as e:
            print(f"損益レポートシート設定エラー: {e}")
            return None

    def setup_currency_sheet(self) -> gspread.Worksheet | None:
        """為替レートシートを初期設定"""
        try:
            try:
                currency_sheet = self.spreadsheet.worksheet(SHEET_NAMES['CURRENCY'])
                print("✅ 為替レートシートは既に存在します")
                return currency_sheet
            except gspread.WorksheetNotFound:
                currency_sheet = self.spreadsheet.add_worksheet(
                    SHEET_NAMES['CURRENCY'], 500, len(HEADERS['CURRENCY'])
                )
                print("💱 新しい為替レートシートを作成しました")

            # ヘッダー設定（共通定義から取得）
            headers = HEADERS['CURRENCY']
            col_range = COLUMN_RANGES['CURRENCY']
            currency_sheet.update(f'{col_range}1', [headers])

            # スタイル設定
            currency_sheet.format(f'{col_range}1', {
                'backgroundColor': {'red': 0.7, 'green': 0.7, 'blue': 0.9},
                'textFormat': {'bold': True}
            })

            print("✅ 為替レートシートの初期設定完了")
            return currency_sheet

        except Exception as e:
            print(f"為替レートシート設定エラー: {e}")
            return None

    def save_currency_rates(
        self, exchange_rates: dict[str, float], date: datetime | None
    ) -> None:
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
                existing_row = self._find_existing_currency_row(
                    existing_records, date_str, currency_pair
                )

                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    currency_sheet.update(
                        f'A{row_number}:H{row_number}', [currency_data]
                    )
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

    def get_portfolio_data(self) -> list[dict[str, object]]:
        """ポートフォリオデータを取得"""
        try:
            portfolio_sheet = self.spreadsheet.worksheet("ポートフォリオ")
            records = portfolio_sheet.get_all_records()
            return records
        except Exception as e:
            print(f"ポートフォリオデータ取得エラー: {e}")
            return []

    def save_data_record(
        self, data_record_results: list[dict[str, object]]
    ) -> None:
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
                existing_row = self._find_existing_row(
                    existing_records, date_str, symbol, 'データ記録'
                )

                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    data_sheet.update(f'A{row_number}:I{row_number}', [data])
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

    def save_performance_data(
        self, performance_results: list[dict[str, object]]
    ) -> None:
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
                existing_row = self._find_existing_row(
                    existing_records, date_str, symbol, '損益レポート'
                )

                if existing_row:
                    # 既存データを更新
                    row_number = existing_row['row_number']
                    perf_sheet.update(f'A{row_number}:P{row_number}', [data])
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

    def display_portfolio_summary(self, year: int, month: int) -> None:
        """ポートフォリオサマリーを表示（重複除去）"""
        try:
            perf_sheet = self.spreadsheet.worksheet("損益レポート")
            records = perf_sheet.get_all_records()

            # 指定月のデータをフィルタリング
            target_date = f"{year}-{month:02d}-末"
            current_data = [r for r in records if r['日付'] == target_date]

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
            pl_mark = '🎉' if total_pl >= 0 else '😢'
            print(
                f"{pl_mark} 総合損益: {total_pl:+,.0f}円 ({total_pl_rate:+.1f}%)"
            )

            print("\n📊 銘柄別詳細:")
            for data in unique_data:
                pl_emoji = "🎉" if data['損益'] >= 0 else "😢"
                print(
                    f"  {pl_emoji} {data['銘柄名']}: "
                    f"{data['損益']:+,.0f}円 ({data['損益率(%)']:+.1f}%)"
                )

        except Exception as e:
            print(f"サマリー表示エラー: {e}")

    def _remove_duplicate_summary_records(
        self, records: list[dict[str, object]]
    ) -> list[dict[str, object]]:
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

    def _find_existing_row(
        self,
        existing_records: list[dict[str, object]],
        date_str: str,
        symbol: str,
        sheet_type: str,
    ) -> dict[str, object] | None:
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
                    # +2はヘッダー行を考慮
                    return {'row_number': i + 2, 'record': record}

            # 損益レポートシートの場合
            elif sheet_type == '損益レポート':
                if (record.get('日付') == date_str and
                    record.get('銘柄コード') == symbol):
                    # +2はヘッダー行を考慮
                    return {'row_number': i + 2, 'record': record}

        return None

    def _find_existing_currency_row(
        self,
        existing_records: list[dict[str, object]],
        date_str: str,
        currency_pair: str,
    ) -> dict[str, object] | None:
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
                # +2はヘッダー行を考慮
                return {'row_number': i + 2, 'record': record}

        return None
