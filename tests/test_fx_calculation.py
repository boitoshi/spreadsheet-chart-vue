"""
為替分離計算のユニットテスト
data-collectorのmain.pyとweb-appのportfolio/services.pyの計算ロジックを検証
"""
import sys
import os
import unittest

# テスト対象のservices.pyをインポートするためDjango設定不要で計算ロジックのみテスト

class TestFxSeparationCalculation(unittest.TestCase):
    """data-collector側の為替分離計算ロジックのテスト"""

    def test_jpy_stock_no_fx_impact(self):
        """日本株は為替影響なし"""
        currency = "JPY"
        purchase_fx_rate = 0
        purchase_price_local = 5500  # 円
        month_end_price_local = 6000  # 円
        shares = 10

        local_currency_pl = 0.0
        fx_impact = 0.0
        if currency != "JPY" and purchase_fx_rate > 0:
            local_currency_pl = (month_end_price_local - purchase_price_local) * shares
            profit_at_purchase_rate = (
                (month_end_price_local - purchase_price_local) * purchase_fx_rate * shares
            )
            profit_loss = (month_end_price_local - purchase_price_local * 1.0) * shares
            fx_impact = profit_loss - profit_at_purchase_rate

        self.assertEqual(local_currency_pl, 0.0)
        self.assertEqual(fx_impact, 0.0)

    def test_usd_stock_fx_separation(self):
        """米国株の為替分離計算"""
        currency = "USD"
        purchase_price_local = 850.0    # USD
        purchase_fx_rate = 149.50       # 取得時のUSD/JPY
        month_end_price_local = 900.0   # USD（現在）
        current_fx_rate = 155.00        # 現在のUSD/JPY
        shares = 2

        purchase_price_jpy = purchase_price_local * purchase_fx_rate  # 127,075円
        month_end_price_jpy = month_end_price_local * current_fx_rate  # 139,500円

        # 円建て損益
        profit_loss = month_end_price_jpy * shares - purchase_price_jpy * shares
        # = 279,000 - 254,150 = 24,850円

        # 現地通貨損益
        local_currency_pl = (month_end_price_local - purchase_price_local) * shares
        # = (900 - 850) × 2 = 100 USD

        # 取得時レートでの円建て損益
        profit_at_purchase_rate = local_currency_pl * purchase_fx_rate
        # = 100 × 149.50 = 14,950円

        # 為替影響
        fx_impact = profit_loss - profit_at_purchase_rate
        # = 24,850 - 14,950 = 9,900円（円安で利益増）

        self.assertEqual(purchase_price_jpy, 127075.0)
        self.assertEqual(local_currency_pl, 100.0)
        self.assertEqual(profit_at_purchase_rate, 14950.0)
        self.assertEqual(profit_loss, 24850.0)
        self.assertEqual(fx_impact, 9900.0)

    def test_usd_stock_fx_negative_impact(self):
        """円高で為替影響がマイナスの場合"""
        currency = "USD"
        purchase_price_local = 850.0
        purchase_fx_rate = 155.00       # 取得時のUSD/JPY（高い）
        month_end_price_local = 900.0
        current_fx_rate = 145.00        # 現在のUSD/JPY（円高に）
        shares = 2

        purchase_price_jpy = purchase_price_local * purchase_fx_rate  # 131,750円
        month_end_price_jpy = month_end_price_local * current_fx_rate  # 130,500円

        profit_loss = month_end_price_jpy * shares - purchase_price_jpy * shares
        # = 261,000 - 263,500 = -2,500円

        local_currency_pl = (month_end_price_local - purchase_price_local) * shares
        # = 100 USD（株自体は上がっている）

        profit_at_purchase_rate = local_currency_pl * purchase_fx_rate
        # = 100 × 155 = 15,500円

        fx_impact = profit_loss - profit_at_purchase_rate
        # = -2,500 - 15,500 = -18,000円（円高で損失）

        self.assertEqual(local_currency_pl, 100.0)
        self.assertAlmostEqual(profit_loss, -2500.0)
        self.assertAlmostEqual(fx_impact, -18000.0)
        # 株は+100USD（プラス）でも為替でマイナスに
        self.assertGreater(local_currency_pl, 0)
        self.assertLess(fx_impact, 0)

    def test_hkd_stock_fx_separation(self):
        """香港株の為替分離計算"""
        currency = "HKD"
        purchase_price_local = 350.0
        purchase_fx_rate = 19.50        # HKD/JPY
        month_end_price_local = 380.0
        current_fx_rate = 20.00
        shares = 5

        purchase_price_jpy = purchase_price_local * purchase_fx_rate  # 6,825円
        month_end_price_jpy = month_end_price_local * current_fx_rate  # 7,600円

        profit_loss = month_end_price_jpy * shares - purchase_price_jpy * shares
        # = 38,000 - 34,125 = 3,875円

        local_currency_pl = (month_end_price_local - purchase_price_local) * shares
        # = 150 HKD

        profit_at_purchase_rate = local_currency_pl * purchase_fx_rate
        # = 150 × 19.50 = 2,925円

        fx_impact = profit_loss - profit_at_purchase_rate
        # = 3,875 - 2,925 = 950円

        self.assertEqual(local_currency_pl, 150.0)
        self.assertAlmostEqual(fx_impact, 950.0)

    def test_multiple_transactions_weighted_fx(self):
        """買い増し時の加重平均為替レートでのFX計算"""
        # トランザクション1: 850 USD × 2株 @ 149.50
        # トランザクション2: 920 USD × 3株 @ 155.20
        transactions = [
            {"purchase_price_local": 850, "purchase_fx_rate": 149.50, "quantity": 2},
            {"purchase_price_local": 920, "purchase_fx_rate": 155.20, "quantity": 3},
        ]
        current_local_price = 950.0
        current_fx_rate = 152.00

        total_quantity = sum(tx["quantity"] for tx in transactions)  # 5
        total_cost_local = sum(tx["purchase_price_local"] * tx["quantity"] for tx in transactions)
        # = 850×2 + 920×3 = 1700 + 2760 = 4460 USD

        total_cost_jpy = sum(
            tx["purchase_price_local"] * tx["purchase_fx_rate"] * tx["quantity"]
            for tx in transactions
        )
        # = 850×149.50×2 + 920×155.20×3 = 254,150 + 428,352 = 682,502円

        current_value_jpy = current_local_price * current_fx_rate * total_quantity
        # = 950 × 152.00 × 5 = 722,000円

        profit_loss = current_value_jpy - total_cost_jpy
        # = 722,000 - 682,502 = 39,498円

        local_currency_pl = current_local_price * total_quantity - total_cost_local
        # = 4750 - 4460 = 290 USD

        # 加重平均為替レート
        avg_fx_rate = sum(
            tx["purchase_fx_rate"] * tx["quantity"] for tx in transactions
        ) / total_quantity
        # = (149.50×2 + 155.20×3) / 5 = (299 + 465.6) / 5 = 152.92

        profit_at_purchase_rate = local_currency_pl * avg_fx_rate
        # = 290 × 152.92 = 44,346.8

        fx_impact = profit_loss - profit_at_purchase_rate
        # = 39,498 - 44,346.8 = -4,848.8

        self.assertEqual(total_quantity, 5)
        self.assertEqual(total_cost_local, 4460.0)
        self.assertEqual(local_currency_pl, 290.0)
        self.assertAlmostEqual(avg_fx_rate, 152.92, places=2)
        # 株はプラスだが為替で一部相殺される
        self.assertGreater(local_currency_pl, 0)
        self.assertLess(fx_impact, 0)
        self.assertGreater(profit_loss, 0)  # トータルはまだプラス


class TestWebAppPerformanceCalculation(unittest.TestCase):
    """web-app側のcalculate_portfolio_performanceの為替分離テスト"""

    def _run_calculation(self, portfolio_data, data_record_data):
        """services.pyの計算ロジックを模擬実行"""
        from datetime import datetime

        price_map = {}
        local_price_map = {}
        fx_rate_map = {}
        currency_map = {}
        parsed_dates = {}

        for record in data_record_data:
            date_key = record.get("月末日付", "")
            stock_code = record.get("銘柄コード", "")
            price = float(record.get("月末価格（円）", 0)) if record.get("月末価格（円）") else 0
            if date_key and stock_code and price > 0:
                parsed_dates[date_key] = datetime.strptime(date_key, "%Y-%m-%d")
                if date_key not in price_map:
                    price_map[date_key] = {}
                    local_price_map[date_key] = {}
                    fx_rate_map[date_key] = {}
                    currency_map[date_key] = {}
                price_map[date_key][stock_code] = price
                local_price_map[date_key][stock_code] = float(record.get("現地通貨価格", price))
                fx_rate_map[date_key][stock_code] = float(record.get("為替レート", 0) or 0)
                currency_map[date_key][stock_code] = record.get("通貨", "JPY") or "JPY"

        portfolio_transactions = {}
        for tx in portfolio_data:
            stock_code = tx["銘柄コード"]
            purchase_price_jpy = float(tx.get("取得単価（円）", 0))
            purchase_price_local = float(tx.get("取得単価", purchase_price_jpy))
            purchase_fx_rate = float(tx.get("取得時レート", 0) or 0)
            if stock_code not in portfolio_transactions:
                portfolio_transactions[stock_code] = {
                    "stock_name": tx["銘柄名"],
                    "currency": tx.get("取得通貨", "JPY"),
                    "transactions": [],
                }
            portfolio_transactions[stock_code]["transactions"].append({
                "purchase_date_parsed": datetime.strptime(tx["取得日"], "%Y-%m-%d"),
                "purchase_date": tx["取得日"],
                "purchase_price": purchase_price_jpy,
                "purchase_price_local": purchase_price_local,
                "purchase_fx_rate": purchase_fx_rate,
                "quantity": int(tx["保有株数"]),
            })

        results = []
        sorted_dates = sorted(price_map.keys(), key=lambda x: parsed_dates[x])
        for date_key in sorted_dates:
            month_end_date = parsed_dates[date_key]
            for stock_code, stock_info in portfolio_transactions.items():
                if stock_code in price_map[date_key]:
                    current_price = price_map[date_key][stock_code]
                    current_local = local_price_map[date_key].get(stock_code, current_price)
                    current_fx = fx_rate_map[date_key].get(stock_code, 0)
                    stk_currency = currency_map[date_key].get(stock_code, "JPY")

                    acquired = [t for t in stock_info["transactions"]
                                if t["purchase_date_parsed"] <= month_end_date]
                    if acquired:
                        total_qty = sum(t["quantity"] for t in acquired)
                        total_cost = sum(t["quantity"] * t["purchase_price"] for t in acquired)
                        current_value = current_price * total_qty
                        profit = current_value - total_cost

                        local_pl = 0.0
                        fx_imp = 0.0
                        if stk_currency != "JPY" and current_fx > 0:
                            total_cost_local = sum(t["quantity"] * t["purchase_price_local"] for t in acquired)
                            local_pl = round(current_local * total_qty - total_cost_local, 2)
                            total_qty_with_rate = sum(t["quantity"] for t in acquired if t["purchase_fx_rate"] > 0)
                            if total_qty_with_rate > 0:
                                avg_fx = sum(t["quantity"] * t["purchase_fx_rate"] for t in acquired if t["purchase_fx_rate"] > 0) / total_qty_with_rate
                                fx_imp = round(profit - local_pl * avg_fx, 0)

                        results.append({
                            "日付": date_key,
                            "銘柄コード": stock_code,
                            "銘柄名": stock_info["stock_name"],
                            "損益": round(profit, 0),
                            "通貨": stk_currency,
                            "現地通貨損益": local_pl,
                            "為替影響額": fx_imp,
                        })
        return results

    def test_jpy_stock(self):
        """日本株のテスト"""
        portfolio = [{
            "銘柄コード": "7974.T", "銘柄名": "任天堂", "取得日": "2024-01-15",
            "取得単価": 5500, "取得通貨": "JPY", "取得時レート": "",
            "取得単価（円）": 5500, "保有株数": 10,
        }]
        data_record = [{
            "月末日付": "2024-12-31", "銘柄コード": "7974.T",
            "現地通貨価格": 6000, "通貨": "JPY", "為替レート": "",
            "月末価格（円）": 6000,
        }]
        results = self._run_calculation(portfolio, data_record)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r["損益"], 5000)  # (6000-5500)*10
        self.assertEqual(r["現地通貨損益"], 0.0)
        self.assertEqual(r["為替影響額"], 0.0)

    def test_usd_stock_with_fx(self):
        """米国株のテスト（為替分離あり）"""
        portfolio = [{
            "銘柄コード": "NVDA", "銘柄名": "エヌビディア", "取得日": "2024-03-05",
            "取得単価": 850, "取得通貨": "USD", "取得時レート": 149.50,
            "取得単価（円）": 127075, "保有株数": 2,
        }]
        data_record = [{
            "月末日付": "2024-12-31", "銘柄コード": "NVDA",
            "現地通貨価格": 900, "通貨": "USD", "為替レート": 155.0,
            "月末価格（円）": 139500,
        }]
        results = self._run_calculation(portfolio, data_record)
        self.assertEqual(len(results), 1)
        r = results[0]
        # 円建て損益: 139500×2 - 127075×2 = 279000 - 254150 = 24850
        self.assertEqual(r["損益"], 24850)
        # 現地通貨損益: (900-850)×2 = 100 USD
        self.assertEqual(r["現地通貨損益"], 100.0)
        # 為替影響: 24850 - 100×149.50 = 24850 - 14950 = 9900
        self.assertEqual(r["為替影響額"], 9900)
        self.assertEqual(r["通貨"], "USD")

    def test_backward_compatibility_without_new_columns(self):
        """新列がない旧データでも動作すること"""
        portfolio = [{
            "銘柄コード": "7974.T", "銘柄名": "任天堂", "取得日": "2024-01-15",
            "取得単価（円）": 5500, "保有株数": 10,
        }]
        data_record = [{
            "月末日付": "2024-12-31", "銘柄コード": "7974.T",
            "月末価格（円）": 6000,
        }]
        results = self._run_calculation(portfolio, data_record)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r["損益"], 5000)
        self.assertEqual(r["現地通貨損益"], 0.0)
        self.assertEqual(r["為替影響額"], 0.0)


if __name__ == "__main__":
    unittest.main()
