"""ブログ記事用レポート生成モジュール（SQLite版）"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .stock_utils import get_currency_from_symbol, is_foreign_stock

if TYPE_CHECKING:
    from .db_writer import DbWriter


class BlogReportGenerator:
    """ブログ記事用レポート生成クラス（SQLite版）"""

    def __init__(self, db_writer: DbWriter) -> None:
        """初期化

        Args:
            db_writer: DbWriterインスタンス
        """
        self.db = db_writer

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
            # 1. ポートフォリオ(holdings)取得
            portfolio_data = self.db.get_portfolio_data()
            if not portfolio_data:
                print("❌ ポートフォリオデータが取得できませんでした")
                return None

            # 2. 損益データ取得（SQLiteのUNIQUE制約で重複なし）
            month_perf_data = self.db.get_performance_data(year, month)
            if not month_perf_data:
                print(f"❌ {year}年{month}月の損益レポートデータが見つかりません")
                return None

            # 3. 市場データ取得（月末日付で）
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            last_day_str = last_day.strftime("%Y-%m-%d")
            month_market_data = self.db.get_market_data(last_day_str)

            # 4. 為替レート取得
            exchange_rates = self.db.get_latest_exchange_rates()

            # 5. 保有銘柄データを構築
            holdings = []
            jp_total_value = 0
            foreign_total_value = 0

            for perf in month_perf_data:
                symbol = perf.get("code", "")
                market_entry = month_market_data.get(symbol, {})

                # ポートフォリオデータから通貨情報を取得
                portfolio_entry = next(
                    (p for p in portfolio_data if p.get("code") == symbol), {}
                )

                # 通貨とフラグを取得（空の場合は自動判定）
                currency = perf.get("currency", "") or portfolio_entry.get(
                    "currency", ""
                )
                is_foreign_flag = portfolio_entry.get("is_foreign", None)

                # 自動判定ロジックを適用
                if not currency or currency == "JPY":
                    currency = get_currency_from_symbol(symbol)

                # 外国株フラグが不明な場合、銘柄コードから判定
                if is_foreign_flag is None:
                    is_foreign = is_foreign_stock(symbol, currency)
                else:
                    # SQLite は 0/1 で格納される場合があるため bool に変換
                    is_foreign = bool(is_foreign_flag)

                # 市場データ
                market_data = {
                    "high": market_entry.get("high", 0),
                    "low": market_entry.get("low", 0),
                    "change_rate": market_entry.get("change_rate", 0),
                }

                # 外貨建て情報を損益レポートから取得
                purchase_price_foreign = perf.get("acquired_price_foreign") or 0
                month_end_price_foreign = perf.get("current_price_foreign") or 0
                purchase_exchange_rate = perf.get("acquired_exchange_rate") or 0
                current_exchange_rate_val = perf.get("current_exchange_rate") or 0

                # ポートフォリオシートからのフォールバック
                if not purchase_price_foreign:
                    raw_foreign = portfolio_entry.get("acquired_price_foreign", 0)
                    purchase_price_foreign = float(raw_foreign) if raw_foreign else 0
                if not purchase_exchange_rate:
                    raw_rate = portfolio_entry.get("acquired_exchange_rate", 0)
                    purchase_exchange_rate = float(raw_rate) if raw_rate else 0

                holding_info = {
                    "name": perf.get("name", ""),
                    "symbol": symbol,
                    "shares": perf.get("shares", 0),
                    "cost_price": perf.get("acquired_price", 0),
                    "current_price": perf.get("current_price", 0),
                    "cost": perf.get("cost", 0),
                    "value": perf.get("value", 0),
                    "pl": perf.get("profit", 0),
                    "pl_rate": perf.get("profit_rate", 0),
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
                    shares_val = perf.get("shares", 0) or 0
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
                value = perf.get("value", 0)
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
                "foreign_stocks": {
                    "value": foreign_total_value,
                    "ratio": foreign_ratio,
                },
                "exchange_rates": exchange_rates,
            }

        except Exception as e:
            print(f"❌ レポートデータ取得エラー: {e}")
            import traceback

            traceback.print_exc()
            return None
