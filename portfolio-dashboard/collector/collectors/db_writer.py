"""SQLite データ書き込みモジュール"""

import sqlite3


class DbWriter:
    """SQLite へのデータ書き込みクラス"""

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")

    def close(self) -> None:
        self.conn.close()

    def save_monthly_price(self, data: dict) -> None:
        """月次市場データを保存（UPSERT）"""
        self.conn.execute(
            """
            INSERT INTO monthly_prices (
                date, code, price_jpy, high, low, average,
                change_rate, avg_volume, created_at)
            VALUES (
                :date, :code, :price_jpy, :high, :low, :average,
                :change_rate, :avg_volume, :created_at)
            ON CONFLICT(date, code) DO UPDATE SET
                price_jpy=excluded.price_jpy, high=excluded.high, low=excluded.low,
                average=excluded.average, change_rate=excluded.change_rate,
                avg_volume=excluded.avg_volume, created_at=excluded.created_at
        """,
            data,
        )
        self.conn.commit()

    def save_monthly_pnl(self, data: dict) -> None:
        """月次損益を保存（UPSERT）"""
        self.conn.execute(
            """
            INSERT INTO monthly_pnl (date, code, name, acquired_price, current_price,
                shares, cost, value, profit, profit_rate, currency,
                acquired_price_foreign, current_price_foreign,
                acquired_exchange_rate, current_exchange_rate, updated_at)
            VALUES (:date, :code, :name, :acquired_price, :current_price,
                :shares, :cost, :value, :profit, :profit_rate, :currency,
                :acquired_price_foreign, :current_price_foreign,
                :acquired_exchange_rate, :current_exchange_rate, :updated_at)
            ON CONFLICT(date, code) DO UPDATE SET
                name=excluded.name, current_price=excluded.current_price,
                value=excluded.value, profit=excluded.profit,
                profit_rate=excluded.profit_rate,
                current_price_foreign=excluded.current_price_foreign,
                current_exchange_rate=excluded.current_exchange_rate,
                updated_at=excluded.updated_at
        """,
            data,
        )
        self.conn.commit()

    def save_exchange_rate(self, data: dict) -> None:
        """為替レートを保存（UPSERT）"""
        self.conn.execute(
            """
            INSERT INTO exchange_rates (
                date, pair, rate, prev_rate, change_rate, high, low, updated_at)
            VALUES (
                :date, :pair, :rate, :prev_rate, :change_rate, :high, :low, :updated_at)
            ON CONFLICT(date, pair) DO UPDATE SET
                rate=excluded.rate, prev_rate=excluded.prev_rate,
                change_rate=excluded.change_rate, high=excluded.high, low=excluded.low,
                updated_at=excluded.updated_at
        """,
            data,
        )
        self.conn.commit()

    def save_benchmark(self, data: dict) -> None:
        """ベンチマークデータを保存（UPSERT）"""
        self.conn.execute(
            """
            INSERT INTO benchmark_data (date, portfolio, nikkei225, sp500)
            VALUES (:date, :portfolio, :nikkei225, :sp500)
            ON CONFLICT(date) DO UPDATE SET
                portfolio=excluded.portfolio, nikkei225=excluded.nikkei225,
                sp500=excluded.sp500
        """,
            data,
        )
        self.conn.commit()

    def get_portfolio_data(self) -> list[dict]:
        """holdings テーブルから保有銘柄を取得"""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute("SELECT * FROM holdings")
        rows = cursor.fetchall()
        self.conn.row_factory = None
        return [dict(row) for row in rows]

    def get_performance_data(self, year: int, month: int) -> list[dict]:
        """指定月の損益データを取得"""
        target_date = f"{year}-{month:02d}-末"
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(
            "SELECT * FROM monthly_pnl WHERE date = ?", (target_date,)
        )
        rows = cursor.fetchall()
        self.conn.row_factory = None
        return [dict(row) for row in rows]

    def get_market_data(self, date_str: str) -> dict[str, dict]:
        """指定日の市場データを銘柄コード→データのdictで取得"""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute(
            "SELECT * FROM monthly_prices WHERE date = ?", (date_str,)
        )
        rows = cursor.fetchall()
        self.conn.row_factory = None
        return {row["code"]: dict(row) for row in rows}

    def get_latest_exchange_rates(self) -> dict[str, float]:
        """最新の為替レートを通貨コード→レートのdictで取得"""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute("""
            SELECT pair, rate FROM exchange_rates
            WHERE date = (SELECT MAX(date) FROM exchange_rates)
        """)
        rows = cursor.fetchall()
        self.conn.row_factory = None
        rates: dict[str, float] = {}
        for row in rows:
            pair = row["pair"]
            if pair.endswith("/JPY"):
                currency = pair.replace("/JPY", "")
                rates[currency] = row["rate"]
        return rates

    def get_all_pnl_data(self) -> list[dict]:
        """全月の損益データを取得（ベンチマーク計算用）"""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.execute("SELECT * FROM monthly_pnl ORDER BY date")
        rows = cursor.fetchall()
        self.conn.row_factory = None
        return [dict(row) for row in rows]

    def display_portfolio_summary(self, year: int, month: int) -> None:
        """ポートフォリオサマリーを表示"""
        records = self.get_performance_data(year, month)
        if not records:
            print("  データなし")
            return
        total_value = sum(r["value"] for r in records)
        total_profit = sum(r["profit"] for r in records)
        total_cost = sum(r["cost"] for r in records)
        profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
        print(f"\n  評価額合計: {total_value:,.0f}円")
        print(f"  損益合計: {total_profit:,.0f}円 ({profit_rate:.2f}%)")
        for r in sorted(records, key=lambda x: x["profit"], reverse=True):
            print(
                f"    {r['name']:10s} {r['profit']:>10,.0f}円 ({r['profit_rate']:.1f}%)"
            )
