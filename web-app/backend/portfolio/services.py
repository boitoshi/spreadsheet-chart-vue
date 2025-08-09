"""
Google Sheets連携サービス
data-collectorとの設定を共有して既存データを読み取り
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict

import gspread
from django.conf import settings
from google.oauth2.service_account import Credentials

# 共通設定をインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
try:
    from sheets_config import HEADERS, SCOPES, SHEET_NAMES
except ImportError:
    # フォールバック設定
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SHEET_NAMES = {
        'PORTFOLIO': 'ポートフォリオ',
        'DATA_RECORD': 'データ記録',
        'PERFORMANCE': '損益レポート'
    }


class ValidationSummary(TypedDict, total=False):
    total_stocks: int
    total_transactions: int
    total_price_records: int
    date_range: RangeSummary
    validation_date: str


class ValidationResult(TypedDict):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    summary: ValidationSummary


class ChartMonthly(TypedDict):
    date: str
    total_profit: float
    total_value: float
    total_cost: float


class RangeSummary(TypedDict):
    start: Optional[str]
    end: Optional[str]
    total_periods: int


class GoogleSheetsService:
    """Google Sheets読み取り専用サービス"""

    def __init__(self) -> None:
        """Google Sheets APIクライアントを初期化"""
        self.gc: Optional[Any] = None
        self.spreadsheet: Optional[Any] = None
        self._setup_credentials()

    def _setup_credentials(self) -> None:
        """Google Sheets認証設定"""
        try:
            if not settings.GOOGLE_APPLICATION_CREDENTIALS:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALSが設定されていません")

            if not settings.SPREADSHEET_ID:
                raise ValueError("SPREADSHEET_IDが設定されていません")

            creds = Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
                scopes=SCOPES
            )
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(settings.SPREADSHEET_ID)

        except Exception as e:
            print(f"Google Sheets認証エラー: {e}")
            raise

    def get_portfolio_data(self) -> List[Dict[str, Any]]:
        """ポートフォリオマスタシートから取引履歴を取得"""
        try:
            assert self.spreadsheet is not None
            portfolio_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PORTFOLIO'])
            records = portfolio_sheet.get_all_records()
            return records  # type: ignore[no-any-return]
        except Exception as e:
            print(f"ポートフォリオデータ取得エラー: {e}")
            return []

    def get_data_record_data(self) -> List[Dict[str, Any]]:
        """データ記録シートから月末価格データを取得"""
        try:
            assert self.spreadsheet is not None
            data_record_sheet = self.spreadsheet.worksheet(SHEET_NAMES['DATA_RECORD'])
            records = data_record_sheet.get_all_records()
            return records  # type: ignore[no-any-return]
        except Exception as e:
            print(f"データ記録シート取得エラー: {e}")
            return []

    def calculate_portfolio_performance(self, portfolio_data: List[Dict[str, Any]], data_record_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ポートフォリオシートとデータ記録シートから時系列を正確に考慮して損益を計算"""
        try:
            from datetime import datetime

            # データ記録シートを月末日付・銘柄コードでインデックス化
            price_map: Dict[str, Dict[str, float]] = {}
            parsed_dates: Dict[str, datetime] = {}  # 日付文字列からdatetimeオブジェクトへのマッピング

            for record in data_record_data:
                date_key = record.get('月末日付', '')
                stock_code = record.get('銘柄コード', '')
                price = float(record.get('月末価格（円）', 0)) if record.get('月末価格（円）') else 0

                if date_key and stock_code and price > 0:
                    # 日付の解析と正規化
                    try:
                        if '-' in date_key:
                            parsed_date = datetime.strptime(date_key, '%Y-%m-%d')
                        elif '/' in date_key:
                            parsed_date = datetime.strptime(date_key, '%Y/%m/%d')
                        else:
                            continue

                        parsed_dates[date_key] = parsed_date

                        if date_key not in price_map:
                            price_map[date_key] = {}
                        price_map[date_key][stock_code] = price
                    except ValueError:
                        print(f"無効な日付形式をスキップ: {date_key}")
                        continue

            # ポートフォリオデータを銘柄・取引別に整理し、取得日でソート
            portfolio_transactions: Dict[str, Dict[str, Any]] = {}
            for transaction in portfolio_data:
                stock_code = transaction.get('銘柄コード', '')
                stock_name = transaction.get('銘柄名', '')
                purchase_date = transaction.get('取得日', '')
                purchase_price = float(transaction.get('取得単価（円）', 0)) if transaction.get('取得単価（円）') else 0
                quantity = int(transaction.get('保有株数', 0)) if transaction.get('保有株数') else 0

                if stock_code and purchase_date and purchase_price > 0 and quantity > 0:
                    # 取得日の解析
                    try:
                        if '/' in purchase_date:
                            parsed_purchase_date = datetime.strptime(purchase_date, '%Y/%m/%d')
                        elif '-' in purchase_date:
                            parsed_purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
                        else:
                            continue
                    except ValueError:
                        print(f"無効な取得日をスキップ: {purchase_date}")
                        continue

                    if stock_code not in portfolio_transactions:
                        portfolio_transactions[stock_code] = {
                            'stock_name': stock_name,
                            'transactions': []
                        }

                    portfolio_transactions[stock_code]['transactions'].append({
                        'purchase_date': purchase_date,
                        'purchase_date_parsed': parsed_purchase_date,
                        'purchase_price': purchase_price,
                        'quantity': quantity
                    })

            # 各銘柄の取引を取得日順にソート
            for stock_code in portfolio_transactions:
                portfolio_transactions[stock_code]['transactions'].sort(
                    key=lambda x: x['purchase_date_parsed']
                )

            # 月末日付を時系列順にソート
            sorted_dates = sorted(price_map.keys(), key=lambda x: parsed_dates[x])

            # 各月末時点での損益計算
            performance_data: List[Dict[str, Any]] = []

            for date_key in sorted_dates:
                month_end_date = parsed_dates[date_key]

                for stock_code, stock_info in portfolio_transactions.items():
                    if stock_code in price_map[date_key]:
                        current_price = price_map[date_key][stock_code]

                        # その月末時点で既に取得済みの取引のみを抽出
                        acquired_transactions = []
                        for tx in stock_info['transactions']:
                            # 月末日以前に取得された取引のみを対象（同日も含む）
                            if tx['purchase_date_parsed'] <= month_end_date:
                                acquired_transactions.append(tx)

                        # 取得済みの取引がある場合のみ損益計算
                        if acquired_transactions:
                            # 累積保有株数と総取得額を計算
                            total_quantity = sum(tx['quantity'] for tx in acquired_transactions)
                            total_cost = sum(tx['quantity'] * tx['purchase_price'] for tx in acquired_transactions)
                            avg_purchase_price = total_cost / total_quantity if total_quantity > 0 else 0

                            # 評価額と損益を計算
                            current_value = current_price * total_quantity
                            profit = current_value - total_cost
                            profit_rate = (profit / total_cost * 100) if total_cost > 0 else 0

                            performance_data.append({
                                '日付': date_key,
                                '銘柄コード': stock_code,
                                '銘柄名': stock_info['stock_name'],
                                '取得単価': round(avg_purchase_price, 2),
                                '月末価格': current_price,
                                '保有株数': total_quantity,
                                '取得額': round(total_cost, 0),
                                '評価額': round(current_value, 0),
                                '損益': round(profit, 0),
                                '損益率(%)': round(profit_rate, 2),
                                '最初の取得日': acquired_transactions[0]['purchase_date'],
                                '取引回数': len(acquired_transactions)
                            })
                        # 取得前の期間では損益データを作成しない（時系列の正確性を保つ）

            print(f"損益計算完了: {len(performance_data)}件のレコードを生成")
            return performance_data

        except Exception as e:
            print(f"損益計算エラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    def validate_data_integrity(self, portfolio_data: List[Dict[str, Any]], data_record_data: List[Dict[str, Any]]) -> ValidationResult:
        """データの整合性と品質を検証"""
        validation_result: ValidationResult = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'summary': {
                'total_stocks': len(set(p.get('銘柄コード', '') for p in portfolio_data if p.get('銘柄コード'))),
                'total_transactions': len(portfolio_data),
                'total_price_records': len(data_record_data),
                'date_range': self._get_date_range(data_record_data),
                'validation_date': datetime.now().isoformat()
            }
        }

        try:
            from datetime import datetime

            # ポートフォリオデータの検証
            portfolio_issues = self._validate_portfolio_data(portfolio_data)
            validation_result['warnings'].extend(portfolio_issues['warnings'])
            validation_result['errors'].extend(portfolio_issues['errors'])

            # データ記録シートの検証
            data_record_issues = self._validate_data_record(data_record_data)
            validation_result['warnings'].extend(data_record_issues['warnings'])
            validation_result['errors'].extend(data_record_issues['errors'])

            # クロス検証（ポートフォリオとデータ記録の整合性）
            cross_validation = self._validate_cross_consistency(portfolio_data, data_record_data)
            validation_result['warnings'].extend(cross_validation['warnings'])
            validation_result['errors'].extend(cross_validation['errors'])

            # エラーがある場合はis_validをFalseに設定
            if validation_result['errors']:
                validation_result['is_valid'] = False

            # サマリー情報
            validation_result['summary'] = {
                'total_stocks': len(set(p.get('銘柄コード', '') for p in portfolio_data if p.get('銘柄コード'))),
                'total_transactions': len(portfolio_data),
                'total_price_records': len(data_record_data),
                'date_range': self._get_date_range(data_record_data),
                'validation_date': datetime.now().isoformat()
            }

            print(f"データ検証完了: エラー{len(validation_result['errors'])}件、警告{len(validation_result['warnings'])}件")

        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"検証処理エラー: {str(e)}")
            print(f"データ検証エラー: {e}")

        return validation_result

    def _validate_portfolio_data(self, portfolio_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """ポートフォリオデータの検証"""
        issues: Dict[str, List[str]] = {'warnings': [], 'errors': []}

        for i, record in enumerate(portfolio_data):
            stock_code = record.get('銘柄コード', '')
            stock_name = record.get('銘柄名', '')
            purchase_date = record.get('取得日', '')
            purchase_price = record.get('取得単価（円）', '')
            quantity = record.get('保有株数', '')

            # 必須フィールドの検証
            if not stock_code:
                issues['errors'].append(f"行{i+1}: 銘柄コードが未入力")
            if not stock_name:
                issues['warnings'].append(f"行{i+1}: 銘柄名が未入力")
            if not purchase_date:
                issues['errors'].append(f"行{i+1}: 取得日が未入力")

            # 日付形式の検証
            if purchase_date:
                try:
                    if '/' in purchase_date:
                        datetime.strptime(purchase_date, '%Y/%m/%d')
                    elif '-' in purchase_date:
                        datetime.strptime(purchase_date, '%Y-%m-%d')
                    else:
                        issues['errors'].append(f"行{i+1}: 取得日の形式が無効 ({purchase_date})")
                except ValueError:
                    issues['errors'].append(f"行{i+1}: 取得日の形式が無効 ({purchase_date})")

            # 価格の検証
            try:
                price_value = float(purchase_price) if purchase_price else 0
                if price_value <= 0:
                    issues['errors'].append(f"行{i+1}: 取得単価が無効 ({purchase_price})")
            except (ValueError, TypeError):
                issues['errors'].append(f"行{i+1}: 取得単価が数値ではない ({purchase_price})")

            # 株数の検証
            try:
                quantity_value = int(quantity) if quantity else 0
                if quantity_value <= 0:
                    issues['errors'].append(f"行{i+1}: 保有株数が無効 ({quantity})")
            except (ValueError, TypeError):
                issues['errors'].append(f"行{i+1}: 保有株数が数値ではない ({quantity})")

        return issues

    def _validate_data_record(self, data_record_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """データ記録シートの検証"""
        issues: Dict[str, List[str]] = {'warnings': [], 'errors': []}

        for i, record in enumerate(data_record_data):
            date_key = record.get('月末日付', '')
            stock_code = record.get('銘柄コード', '')
            price = record.get('月末価格（円）', '')

            # 必須フィールドの検証
            if not date_key:
                issues['errors'].append(f"データ記録行{i+1}: 月末日付が未入力")
            if not stock_code:
                issues['errors'].append(f"データ記録行{i+1}: 銘柄コードが未入力")

            # 日付形式の検証
            if date_key:
                try:
                    if '-' in date_key:
                        datetime.strptime(date_key, '%Y-%m-%d')
                    elif '/' in date_key:
                        datetime.strptime(date_key, '%Y/%m/%d')
                    else:
                        issues['errors'].append(f"データ記録行{i+1}: 日付形式が無効 ({date_key})")
                except ValueError:
                    issues['errors'].append(f"データ記録行{i+1}: 日付形式が無効 ({date_key})")

            # 価格の検証
            try:
                price_value = float(price) if price else 0
                if price_value <= 0:
                    issues['warnings'].append(f"データ記録行{i+1}: 月末価格が0または未入力 ({price})")
            except (ValueError, TypeError):
                issues['errors'].append(f"データ記録行{i+1}: 月末価格が数値ではない ({price})")

        return issues

    def _validate_cross_consistency(self, portfolio_data: List[Dict[str, Any]], data_record_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """ポートフォリオとデータ記録の整合性検証"""
        issues: Dict[str, List[str]] = {'warnings': [], 'errors': []}

        # ポートフォリオに含まれる銘柄コード
        portfolio_stocks = set(p.get('銘柄コード', '') for p in portfolio_data if p.get('銘柄コード'))

        # データ記録に含まれる銘柄コード
        data_record_stocks = set(d.get('銘柄コード', '') for d in data_record_data if d.get('銘柄コード'))

        # ポートフォリオにあるがデータ記録にない銘柄
        missing_price_data = portfolio_stocks - data_record_stocks
        for stock_code in missing_price_data:
            issues['errors'].append(f"銘柄{stock_code}: ポートフォリオに存在するが価格データが不足")

        # データ記録にあるがポートフォリオにない銘柄
        extra_price_data = data_record_stocks - portfolio_stocks
        for stock_code in extra_price_data:
            issues['warnings'].append(f"銘柄{stock_code}: 価格データは存在するがポートフォリオに未登録")

        # 各銘柄の価格データ期間の確認
        for stock_code in portfolio_stocks:
            # 最早取得日を取得
            stock_transactions = [p for p in portfolio_data if p.get('銘柄コード') == stock_code]
            if stock_transactions:
                parsed = [
                    d for d in (self._parse_date(tx.get('取得日', '')) for tx in stock_transactions)
                    if d is not None
                ]
                earliest_date = min(parsed) if parsed else None

                # 該当銘柄の価格データを確認
                price_records = [d for d in data_record_data if d.get('銘柄コード') == stock_code]
                if price_records:
                    price_dates_all = [self._parse_date(d.get('月末日付', '')) for d in price_records]
                    price_dates = [pd for pd in price_dates_all if pd is not None]
                    if price_dates and earliest_date is not None:
                        latest_price_date = max(price_dates)
                        if latest_price_date < earliest_date:
                            issues['warnings'].append(f"銘柄{stock_code}: 価格データが取得日より古い")

        return issues

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """日付文字列をdatetimeオブジェクトに変換"""
        if not date_str:
            return None
        try:
            if '/' in date_str:
                return datetime.strptime(date_str, '%Y/%m/%d')
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass
        return None

    def _get_date_range(self, data_record_data: List[Dict[str, Any]]) -> RangeSummary:
        """データ記録の日付範囲を取得"""
        dates: List[datetime] = []
        for record in data_record_data:
            date_obj = self._parse_date(record.get('月末日付', ''))
            if date_obj:
                dates.append(date_obj)

        if dates:
            return RangeSummary(
                start=min(dates).strftime('%Y-%m-%d'),
                end=max(dates).strftime('%Y-%m-%d'),
                total_periods=len({d.strftime('%Y-%m') for d in dates}),
            )
        else:
            return RangeSummary(start=None, end=None, total_periods=0)

    def get_performance_history(self, period: str = 'all') -> List[ChartMonthly]:
        """損益推移履歴を期間指定で取得（重複除去）"""
        try:
            assert self.spreadsheet is not None
            performance_sheet = self.spreadsheet.worksheet(SHEET_NAMES['PERFORMANCE'])
            records = performance_sheet.get_all_records()

            if not records:
                return []

            # 期間フィルタリング
            filtered_records = self._filter_by_period(records, period)

            # 日付・銘柄の重複除去
            deduplicated_records = self._remove_duplicates_by_date_stock(filtered_records)

            # 日付でグループ化して月次サマリーを作成
            monthly_summary = self._create_monthly_summary(deduplicated_records)

            return monthly_summary

        except Exception as e:
            print(f"履歴データ取得エラー: {e}")
            return []

    def _filter_by_period(self, records: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        """期間に基づいてレコードをフィルタリング"""
        if period == 'all':
            return records

        now = datetime.now()

        if period == '6months':
            cutoff_date = now - timedelta(days=180)
        elif period == '1year':
            cutoff_date = now - timedelta(days=365)
        else:
            return records

        # 日付文字列をパースしてフィルタリング
        filtered = []
        for record in records:
            try:
                # 日付形式を想定: "2024-01-末" or "2024-01-31"
                date_str = str(record['日付']).replace('-末', '-01')
                record_date = datetime.strptime(date_str[:10], '%Y-%m-%d')

                if record_date >= cutoff_date:
                    filtered.append(record)
            except (ValueError, TypeError):
                continue

        return filtered

    def _create_monthly_summary(self, records: List[Dict[str, Any]]) -> List[ChartMonthly]:
        """月次サマリーを作成（Vue.jsのチャート用）"""
        monthly_data: Dict[str, ChartMonthly] = {}

        for record in records:
            try:
                date_key = str(record['日付'])

                if date_key not in monthly_data:
                    monthly_data[date_key] = ChartMonthly(
                        date=date_key,
                        total_profit=0.0,
                        total_value=0.0,
                        total_cost=0.0,
                    )

                # 数値型に変換（エラー回避）
                profit = float(record.get('損益', 0) or 0)
                value = float(record.get('評価額', 0) or 0)
                cost = float(record.get('取得額', 0) or 0)

                monthly_data[date_key]['total_profit'] += profit
                monthly_data[date_key]['total_value'] += value
                monthly_data[date_key]['total_cost'] += cost

            except (ValueError, TypeError, KeyError):
                continue

        # 日付でソート
        sorted_data = sorted(monthly_data.values(), key=lambda x: x['date'])
        return sorted_data

    def _remove_duplicate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同じ銘柄コードの重複レコードを除去（最新更新日時を優先）"""
        stock_records: Dict[str, Dict[str, Any]] = {}

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

    def _remove_duplicates_by_date_stock(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """日付・銘柄コードの組み合わせで重複レコードを除去（最新更新日時を優先）"""
        unique_records: Dict[str, Dict[str, Any]] = {}

        for record in records:
            date_str = record.get('日付', '')
            stock_code = record.get('銘柄コード', '')

            if not date_str or not stock_code:
                continue

            # 日付・銘柄コードの組み合わせをキーとする
            key = f"{date_str}_{stock_code}"

            # 更新日時を取得（文字列として比較）
            update_time = record.get('更新日時', '')

            # 既存レコードがないか、より新しい更新日時の場合に更新
            if (key not in unique_records or
                update_time > unique_records[key].get('更新日時', '')):
                unique_records[key] = record

        return list(unique_records.values())


class PortfolioDataTransformer:
    """Google SheetsデータをVue.js形式に変換"""

    @staticmethod
    def transform_to_vue_format(portfolio_data: List[Dict[str, Any]], performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Google Sheetsの複数シートデータをVue.jsダッシュボード期待形式に変換
        
        Args:
            portfolio_data: ポートフォリオマスタシートのデータ
            performance_data: 損益レポートシートの最新データ
            
        Returns:
            Vue.js App.vue が期待するデータ形式
        """
        stocks: List[Dict[str, Any]] = []

        # 銘柄別にグループ化
        stock_groups = PortfolioDataTransformer._group_by_stock(portfolio_data)

        # 損益データをマッピング用辞書に変換
        performance_map = {p['銘柄名']: p for p in performance_data}

        for stock_name, transactions in stock_groups.items():
            # パフォーマンスデータから現在価格と損益情報取得
            perf_data = performance_map.get(stock_name, {})
            current_price = float(perf_data.get('月末価格', 0)) if perf_data.get('月末価格') else 0

            # Vue.js形式の取引履歴に変換
            vue_transactions: List[Dict[str, Any]] = []
            total_quantity: int = 0
            total_cost: float = 0.0

            for tx in transactions:
                quantity = int(tx.get('保有株数', 0)) if tx.get('保有株数') else 0
                price = float(tx.get('取得単価（円）', 0)) if tx.get('取得単価（円）') else 0
                date = PortfolioDataTransformer._format_date(tx.get('取得日', ''))

                vue_transactions.append({
                    'date': date,
                    'quantity': quantity,
                    'price': price
                })

                total_quantity += quantity
                total_cost += quantity * price

            # 平均取得価格計算
            avg_price = total_cost / total_quantity if total_quantity > 0 else 0

            # 現在の評価額と損益計算
            current_value = current_price * total_quantity
            profit = current_value - total_cost

            stocks.append({
                'name': stock_name,
                'currentPrice': current_price,
                'transactions': vue_transactions,
                'quantity': total_quantity,
                'avgPrice': round(avg_price, 0),
                'currentValue': round(current_value, 0),
                'profit': round(profit, 0),
                'totalCost': round(total_cost, 0)
            })

        # サマリー計算
        total_value = float(sum(float(s.get('currentValue', 0) or 0) for s in stocks))
        total_cost = float(sum(float(s.get('totalCost', 0) or 0) for s in stocks))
        total_profit = total_value - total_cost

        return {
            'summary': {
                'totalValue': round(total_value, 0),
                'totalProfit': round(total_profit, 0),
                'totalCost': round(total_cost, 0)
            },
            'stocks': stocks
        }

    @staticmethod
    def _group_by_stock(portfolio_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """銘柄名でポートフォリオデータをグループ化"""
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for record in portfolio_data:
            stock_name = record.get('銘柄名', '')
            if not stock_name:
                continue

            if stock_name not in groups:
                groups[stock_name] = []

            groups[stock_name].append(record)

        return groups

    @staticmethod
    def _format_date(date_str: str) -> str:
        """日付形式をVue.js期待形式に変換 (YYYY-MM-DD → YYYY/MM/DD)"""
        try:
            if not date_str:
                return ''

            # 様々な日付形式に対応
            date_str = str(date_str).strip()

            if '-' in date_str:
                # 2024-01-15 → 2024/01/15
                return date_str.replace('-', '/')

            return date_str

        except Exception:
            return date_str
