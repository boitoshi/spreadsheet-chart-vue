"""ブログ記事用レポート生成モジュール"""

from datetime import datetime
from typing import Any

from .stock_utils import get_currency_from_symbol, is_foreign_stock


class BlogReportGenerator:
    """ブログ記事用レポート生成クラス"""

    def __init__(self, sheets_writer: Any) -> None:
        """初期化

        Args:
            sheets_writer: SheetsDataWriterインスタンス
        """
        self.sheets_writer = sheets_writer

    def get_monthly_report_data(self, year: int, month: int) -> dict | None:
        """月次レポートデータを取得

        Args:
            year: 年
            month: 月

        Returns:
            レポートデータ辞書、取得失敗時はNone
            {
                "month": "2024年12月",
                "year": 2024,
                "month_num": 12,
                "total_cost": 合計取得額,
                "total_value": 合計評価額,
                "total_pl": 総損益額,
                "total_pl_rate": 総損益率,
                "holdings": [
                    {
                        "name": "任天堂",
                        "symbol": "7974.T",
                        "shares": 10,
                        "cost_price": 5500,
                        "current_price": 6500,
                        "cost": 55000,
                        "value": 65000,
                        "pl": 10000,
                        "pl_rate": 18.18,
                        "currency": "JPY",
                        "is_foreign": False,
                        "market_data": {
                            "high": 6800,
                            "low": 6200,
                            "change_rate": 5.2
                        }
                    },
                    # ...
                ],
                "jp_stocks": {
                    "value": 日本株評価額,
                    "ratio": 日本株比率
                },
                "foreign_stocks": {
                    "value": 外国株評価額,
                    "ratio": 外国株比率
                },
                "exchange_rates": {
                    "USD": 150.25,
                    "HKD": 19.35,
                    # ...
                }
            }
        """
        try:
            # ポートフォリオデータ取得
            portfolio_data = self.sheets_writer.get_portfolio_data()
            if not portfolio_data:
                print("❌ ポートフォリオデータが取得できませんでした")
                return None

            # 損益レポートデータ取得
            perf_sheet = self.sheets_writer.spreadsheet.worksheet("損益レポート")
            perf_records = perf_sheet.get_all_records()

            # データ記録（市場データ）取得
            data_sheet = self.sheets_writer.spreadsheet.worksheet("データ記録")
            data_records = data_sheet.get_all_records()

            # 為替レートデータ取得
            currency_sheet = self.sheets_writer.spreadsheet.worksheet("為替レート")
            currency_records = currency_sheet.get_all_records()

            # 指定月のデータをフィルタリング
            target_date = f"{year}-{month:02d}-末"
            month_perf_data = [
                r for r in perf_records if r.get("日付") == target_date
            ]

            if not month_perf_data:
                print(f"❌ {year}年{month}月の損益レポートデータが見つかりません")
                return None

            # 重複除去
            month_perf_data = self._remove_duplicates(month_perf_data)

            # 月末日付でデータ記録をフィルタリング
            from datetime import timedelta

            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)

            last_day_str = last_day.strftime("%Y-%m-%d")
            month_market_data = {
                r.get("銘柄コード"): r
                for r in data_records
                if r.get("月末日付") == last_day_str
            }

            # 為替レート取得（最新のもの）
            exchange_rates = self._get_latest_exchange_rates(currency_records)

            # 保有銘柄データを構築
            holdings = []
            jp_total_value = 0
            foreign_total_value = 0

            for perf in month_perf_data:
                symbol = perf.get("銘柄コード", "")
                market_data_entry = month_market_data.get(symbol, {})

                # ポートフォリオデータから通貨情報を取得
                portfolio_entry = next(
                    (p for p in portfolio_data if p.get("銘柄コード") == symbol), {}
                )

                # 通貨とフラグを取得（空の場合は自動判定）
                currency = portfolio_entry.get("通貨", "")
                foreign_flag = portfolio_entry.get("外国株フラグ", "")

                # 自動判定ロジックを適用
                if not currency or currency == "JPY":
                    currency = get_currency_from_symbol(symbol)

                # 外国株フラグが空または不明な場合、銘柄コードから判定
                if not foreign_flag or foreign_flag not in ["○", "×"]:
                    is_foreign = is_foreign_stock(symbol, currency)
                else:
                    is_foreign = foreign_flag == "○"

                # 市場データ
                market_data = {
                    "high": market_data_entry.get("最高値", 0),
                    "low": market_data_entry.get("最安値", 0),
                    "change_rate": market_data_entry.get("月間変動率(%)", 0),
                }

                # 外貨建て情報を損益レポートまたはポートフォリオから取得
                purchase_price_foreign = perf.get("取得単価（外貨）", 0) or 0
                month_end_price_foreign = perf.get("月末価格（外貨）", 0) or 0
                purchase_exchange_rate = perf.get("取得時為替レート", 0) or 0
                current_exchange_rate_val = perf.get("現在為替レート", 0) or 0

                # ポートフォリオシートからのフォールバック
                if not purchase_price_foreign:
                    raw_foreign = portfolio_entry.get("取得単価（外貨）", 0)
                    purchase_price_foreign = float(raw_foreign) if raw_foreign else 0
                if not purchase_exchange_rate:
                    raw_rate = portfolio_entry.get("取得時為替レート", 0)
                    purchase_exchange_rate = float(raw_rate) if raw_rate else 0

                holding_info = {
                    "name": perf.get("銘柄名", ""),
                    "symbol": symbol,
                    "shares": perf.get("保有株数", 0),
                    "cost_price": perf.get("取得単価", 0),
                    "current_price": perf.get("月末価格", 0),
                    "cost": perf.get("取得額", 0),
                    "value": perf.get("評価額", 0),
                    "pl": perf.get("損益", 0),
                    "pl_rate": perf.get("損益率(%)", 0),
                    "currency": currency,
                    "is_foreign": is_foreign,
                    "market_data": market_data,
                }

                # 外貨建て情報を追加
                if purchase_price_foreign:
                    holding_info["purchase_price_foreign"] = float(
                        purchase_price_foreign
                    )
                if purchase_exchange_rate:
                    holding_info["purchase_exchange_rate"] = float(
                        purchase_exchange_rate
                    )
                if month_end_price_foreign:
                    holding_info["month_end_price_foreign"] = float(
                        month_end_price_foreign
                    )
                if current_exchange_rate_val:
                    holding_info["current_exchange_rate"] = float(
                        current_exchange_rate_val
                    )

                # 為替レート情報を追加
                if currency != "JPY" and currency in exchange_rates:
                    holding_info["exchange_rate"] = exchange_rates[currency]

                    # 為替損益分離計算（外貨情報が揃っている場合）
                    shares_val = perf.get("保有株数", 0) or 0
                    has_fx_data = (
                        purchase_price_foreign
                        and purchase_exchange_rate
                        and month_end_price_foreign
                    )
                    if has_fx_data:
                        stock_pl = (
                            (
                                float(month_end_price_foreign)
                                - float(purchase_price_foreign)
                            )
                            * float(purchase_exchange_rate)
                            * float(shares_val)
                        )
                        fx_rate = float(
                            current_exchange_rate_val or exchange_rates[currency]
                        )
                        fx_pl = (
                            (fx_rate - float(purchase_exchange_rate))
                            * float(month_end_price_foreign)
                            * float(shares_val)
                        )
                        holding_info["stock_profit_loss"] = round(stock_pl, 0)
                        holding_info["fx_profit_loss"] = round(fx_pl, 0)

                holdings.append(holding_info)

                # 日本株/外国株の分類
                value = perf.get("評価額", 0)
                if is_foreign:
                    foreign_total_value += value
                else:
                    jp_total_value += value

            # 合計値計算
            total_cost = sum(h["cost"] for h in holdings)
            total_value = sum(h["value"] for h in holdings)
            total_pl = total_value - total_cost
            total_pl_rate = (total_pl / total_cost * 100) if total_cost > 0 else 0

            total_value_float = float(total_value)
            jp_ratio = (
                (jp_total_value / total_value_float * 100)
                if total_value_float > 0
                else 0
            )
            foreign_ratio = (
                (foreign_total_value / total_value_float * 100)
                if total_value_float > 0
                else 0
            )

            return {
                "month": f"{year}年{month}月",
                "year": year,
                "month_num": month,
                "total_cost": total_cost,
                "total_value": total_value,
                "total_pl": total_pl,
                "total_pl_rate": total_pl_rate,
                "holdings": holdings,
                "jp_stocks": {"value": jp_total_value, "ratio": jp_ratio},
                "foreign_stocks": {"value": foreign_total_value, "ratio": foreign_ratio},
                "exchange_rates": exchange_rates,
            }

        except Exception as e:
            print(f"❌ レポートデータ取得エラー: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _remove_duplicates(self, records: list) -> list:
        """重複レコードを除去（最新の更新日時のもののみ残す）"""
        stock_records = {}

        for record in records:
            stock_code = record.get("銘柄コード", "")
            if not stock_code:
                continue

            update_time = record.get("更新日時", "")

            if stock_code not in stock_records or update_time > stock_records[
                stock_code
            ].get("更新日時", ""):
                stock_records[stock_code] = record

        return list(stock_records.values())

    def _get_latest_exchange_rates(self, currency_records: list) -> dict:
        """最新の為替レートを取得

        Args:
            currency_records: 為替レートシートのレコードリスト

        Returns:
            通貨コードをキーとしたレート辞書
        """
        rates = {}

        # 最新の日付のレートを取得
        for record in currency_records:
            currency_pair = record.get("通貨ペア", "")
            if not currency_pair or not currency_pair.endswith("/JPY"):
                continue

            currency = currency_pair.replace("/JPY", "")
            rate = record.get("レート", 0)

            # より新しいデータがあれば更新
            if currency not in rates or record.get("取得日", "") > rates.get(
                f"{currency}_date", ""
            ):
                rates[currency] = rate
                rates[f"{currency}_date"] = record.get("取得日", "")

        # 日付情報を削除
        rates = {k: v for k, v in rates.items() if not k.endswith("_date")}

        return rates
