"""ベンチマーク（日経225/S&P500）データ収集モジュール"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import yfinance as yf

from .db_writer import DbWriter


class BenchmarkCollector:
    """月次ベンチマークデータ収集・保存"""

    def __init__(self, db_writer: DbWriter) -> None:
        self.db = db_writer

    def collect(self, year: int, month: int) -> None:
        """指定月までのベンチマークデータを計算・保存"""
        print("\nベンチマークデータを計算中...")

        # ポートフォリオの月次リターン計算
        all_pnl = self.db.get_all_pnl_data()
        if not all_pnl:
            print("  警告: 損益データがありません")
            return

        # 月別に集計: { date: { total_value, total_cost } }
        monthly_agg: dict[str, dict[str, float]] = defaultdict(
            lambda: {"value": 0.0, "cost": 0.0}
        )
        for row in all_pnl:
            monthly_agg[row["date"]]["value"] += row["value"]
            monthly_agg[row["date"]]["cost"] += row["cost"]

        dates = sorted(monthly_agg.keys())
        if not dates:
            return

        # ポートフォリオ累積リターン（初月基準）
        first_cost = monthly_agg[dates[0]]["cost"]
        portfolio_returns: dict[str, float] = {}
        for d in dates:
            agg = monthly_agg[d]
            rate = (
                ((agg["value"] - first_cost) / first_cost * 100)
                if first_cost > 0
                else 0.0
            )
            portfolio_returns[d] = round(rate, 2)

        # 日経225 / S&P500 の月次終値を取得
        nikkei_returns = self._fetch_index_returns("^N225", dates)
        sp500_returns = self._fetch_index_returns("^GSPC", dates)

        # benchmark_data に保存
        for d in dates:
            self.db.save_benchmark(
                {
                    "date": d,
                    "portfolio": portfolio_returns.get(d, 0.0),
                    "nikkei225": nikkei_returns.get(d),
                    "sp500": sp500_returns.get(d),
                }
            )

        print(f"  ベンチマークデータ {len(dates)} 件保存しました")

    def _fetch_index_returns(
        self, symbol: str, dates: list[str]
    ) -> dict[str, float | None]:
        """指数の累積リターンを取得（初月基準）"""
        try:
            # 日付範囲を YYYY-MM-末 形式から推定
            # 最初の月の開始〜最後の月の終了
            first_parts = dates[0].split("-")
            last_parts = dates[-1].split("-")
            start_year, start_month = int(first_parts[0]), int(first_parts[1])
            end_year, end_month = int(last_parts[0]), int(last_parts[1])

            start_date = datetime(start_year, start_month, 1)
            if end_month == 12:
                end_date = datetime(end_year + 1, 1, 1)
            else:
                end_date = datetime(end_year, end_month + 1, 1)

            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date, interval="1mo")

            if hist.empty:
                print(f"  警告: {symbol} のデータが取得できませんでした")
                return dict.fromkeys(dates)

            # 月末価格のマッピング (YYYY-MM → 終値)
            monthly_prices: dict[str, float] = {}
            for idx, row in hist.iterrows():
                ym = idx.strftime("%Y-%m")
                monthly_prices[ym] = float(row["Close"])

            # 初月基準の累積リターン
            first_ym = f"{start_year}-{start_month:02d}"
            first_price = monthly_prices.get(first_ym)
            if first_price is None or first_price == 0:
                return dict.fromkeys(dates)

            returns: dict[str, float | None] = {}
            for d in dates:
                parts = d.split("-")
                ym = f"{parts[0]}-{parts[1]}"
                price = monthly_prices.get(ym)
                if price is not None:
                    returns[d] = round((price - first_price) / first_price * 100, 2)
                else:
                    returns[d] = None

            return returns

        except Exception as e:
            print(f"  警告: {symbol} の取得エラー: {e}")
            return dict.fromkeys(dates)
