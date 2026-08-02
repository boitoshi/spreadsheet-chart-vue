# /// script
# requires-python = ">=3.12"
# dependencies = ["requests"]
# ///
"""月末為替レートを ECB 参照レートに統一し、外貨建て銘柄の円換算値を再計算する。

背景:
    stock_collector は `get_exchange_rate(currency)` を date 引数なしで呼ぶため、
    過去月をあとからバッチ収集すると「実行日のスポットレート」が保存される。
    2026-04/05/06 が 7/8 実行時の 162.57 で固定されているのがその痕跡。

このスクリプトが直すもの（外貨建て銘柄のみ。円建て銘柄は為替 1.0 なので対象外）:
    exchange_rates.rate
    monthly_prices.price_jpy / high / low / average
    monthly_pnl.current_exchange_rate / current_price / value / profit / profit_rate

直さないもの:
    change_rate（外貨ベースの月初→月末騰落率。為替と無関係）
    acquired_* 系（取得時レートは purchase_history のユーザー入力値が正）
    benchmark_data.portfolio（記事には出ない。次回の月次収集で再計算される）

重要:
    monthly_prices と monthly_pnl が「同じレートで書かれている」とは限らない。
    2025-08〜2026-01 は prices が当時のスポット、pnl が後日のバックフィル値で
    書かれており、旧レートが食い違う。よって割り戻しに使う旧レートは
    テーブルごとに行から復元する（pnl の値を流用しない）。

実行:
    uv run repair_fx.py --db /path/to/portfolio.db            # ドライラン（既定）
    uv run repair_fx.py --db /path/to/portfolio.db --apply    # 書き込み
"""

from __future__ import annotations

import argparse
import calendar
import sqlite3
import sys
from datetime import date, datetime

import requests

ECB_API = "https://api.frankfurter.dev/v1/{d}"
TIMEOUT = 30
# collector は保存値を小数2桁に丸めるので合わせる（stock_collector.py 146-162行）
DECIMALS = 2


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def fetch_ecb_rate(base: str, quote: str, on: date) -> tuple[float, str]:
    """ECB 参照レートを取得する。

    frankfurter は指定日が非営業日なら直前の営業日の値を返し、
    レスポンスの date にその実際の日付が入る。
    """
    res = requests.get(
        ECB_API.format(d=on.isoformat()),
        params={"base": base, "symbols": quote},
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    payload = res.json()
    rate = payload["rates"].get(quote)
    if rate is None:
        raise RuntimeError(f"{base}/{quote} のレートが取得できません（{on}）")
    return float(rate), payload["date"]


def parse_pnl_date(pnl_date: str) -> tuple[int, int]:
    """'YYYY-MM-末' から年月を取り出す。"""
    year_s, month_s, _ = pnl_date.split("-")
    return int(year_s), int(month_s)


def build_plan(conn: sqlite3.Connection) -> list[dict]:
    """外貨建て行ごとに、ECB レートで揃えた目標値を組み立てる。"""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT date, code, currency, shares, cost,
               current_price_foreign, current_exchange_rate,
               current_price, value, profit, profit_rate
        FROM monthly_pnl
        WHERE currency IS NOT NULL AND currency <> 'JPY'
        ORDER BY date, code
        """
    ).fetchall()

    rate_cache: dict[str, tuple[float, str]] = {}
    plan: list[dict] = []

    for row in rows:
        year, month = parse_pnl_date(row["date"])
        price_date = month_end(year, month)
        cache_key = f"{row['currency']}-{year}-{month:02d}"
        if cache_key not in rate_cache:
            rate_cache[cache_key] = fetch_ecb_rate(row["currency"], "JPY", price_date)
        new_rate, effective_date = rate_cache[cache_key]

        foreign = float(row["current_price_foreign"] or 0)
        if foreign <= 0:
            print(f"⚠️ {row['date']} {row['code']}: 外貨建て価格が不正のため除外")
            continue

        shares = float(row["shares"])
        cost = float(row["cost"])
        new_price = round(foreign * new_rate, DECIMALS)
        new_value = round(foreign * new_rate * shares, DECIMALS)
        new_profit = round(new_value - cost, DECIMALS)
        new_profit_rate = round(
            (new_profit / cost * 100) if cost > 0 else 0.0, DECIMALS
        )

        # monthly_prices 側は「その行が実際に使ったレート」を行から復元する。
        # pnl の current_exchange_rate を流用すると、両テーブルが別バッチで
        # 書かれた月（2025-08〜2026-01）で誤った外貨値を復元してしまう。
        price_row = conn.execute(
            "SELECT price_jpy, high, low, average FROM monthly_prices "
            "WHERE date = ? AND code = ?",
            (price_date.isoformat(), row["code"]),
        ).fetchone()

        price_update: dict[str, float] | None = None
        if price_row is None:
            print(f"⚠️ monthly_prices に行がありません: {price_date} {row['code']}")
        else:
            implied_old = float(price_row["price_jpy"]) / foreign
            if implied_old <= 0:
                print(f"⚠️ {price_date} {row['code']}: 旧レートを復元できません")
            else:
                # price_jpy は pnl の current_price と同一値を直接入れる。
                # 割り戻し経由にすると丸め誤差で毎回 0.01 だけ揺れて冪等でなくなる
                factor = new_rate / implied_old
                price_update = {"price_jpy": new_price}
                for col in ("high", "low", "average"):
                    if price_row[col] is not None:
                        price_update[col] = round(
                            float(price_row[col]) * factor, DECIMALS
                        )

        # high/low/average は割り戻しを挟むので、保存精度（0.01）未満の
        # 揺れを「変更あり」と見なすと再実行のたびに書き換わってしまう
        eps = 10 ** -DECIMALS * 2
        unchanged = (
            abs(float(row["current_exchange_rate"] or 0) - new_rate) < 1e-9
            and abs(float(row["current_price"]) - new_price) < eps
            and abs(float(row["value"]) - new_value) < eps
            and abs(float(row["profit"]) - new_profit) < eps
            and (
                price_update is None
                or all(
                    abs(float(price_row[col]) - val) < eps
                    for col, val in price_update.items()
                )
            )
        )
        if unchanged:
            continue

        plan.append(
            {
                "pnl_date": row["date"],
                "price_date": price_date.isoformat(),
                "code": row["code"],
                "currency": row["currency"],
                "old_rate": float(row["current_exchange_rate"] or 0),
                "new_rate": new_rate,
                "effective_date": effective_date,
                "old_value": float(row["value"]),
                "new_value": new_value,
                "old_profit_rate": float(row["profit_rate"]),
                "new_profit_rate": new_profit_rate,
                "new_price": new_price,
                "new_profit": new_profit,
                "price_update": price_update,
            }
        )

    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="portfolio.db のパス")
    parser.add_argument(
        "--apply", action="store_true", help="実際に書き込む（既定はドライラン）"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    plan = build_plan(conn)

    if not plan:
        print("修正が必要な行はありません。")
        return 0

    print(
        f"{'月':<12} {'銘柄':<6} {'旧レート':>9} {'新レート':>9} "
        f"{'ECB日付':<12} {'評価額差':>10} {'損益率':>16}  prices"
    )
    print("-" * 92)
    for c in plan:
        marker = "更新" if c["price_update"] else "なし"
        print(
            f"{c['pnl_date']:<12} {c['code']:<6} "
            f"{c['old_rate']:>9.3f} {c['new_rate']:>9.3f} "
            f"{c['effective_date']:<12} "
            f"{c['new_value'] - c['old_value']:>+10,.0f} "
            f"{c['old_profit_rate']:>7.2f}% → {c['new_profit_rate']:>6.2f}%  {marker}"
        )

    if not args.apply:
        print(f"\nドライラン: {len(plan)}件。書き込むには --apply を付ける。")
        return 0

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    try:
        with conn:
            for c in plan:
                pair = f"{c['currency']}/JPY"
                # 行が無い月もあるので UPSERT にする（UPDATE だと無言で空振りする）
                conn.execute(
                    """
                    INSERT INTO exchange_rates (date, pair, rate, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(date, pair) DO UPDATE SET
                        rate = excluded.rate, updated_at = excluded.updated_at
                    """,
                    (c["price_date"], pair, c["new_rate"], now),
                )
                if c["price_update"]:
                    cols = ", ".join(f"{col} = ?" for col in c["price_update"])
                    conn.execute(
                        f"UPDATE monthly_prices SET {cols} WHERE date = ? AND code = ?",
                        (
                            *c["price_update"].values(),
                            c["price_date"],
                            c["code"],
                        ),
                    )
                conn.execute(
                    """
                    UPDATE monthly_pnl
                    SET current_exchange_rate = ?,
                        current_price = ?,
                        value = ?,
                        profit = ?,
                        profit_rate = ?,
                        updated_at = ?
                    WHERE date = ? AND code = ?
                    """,
                    (
                        c["new_rate"], c["new_price"], c["new_value"],
                        c["new_profit"], c["new_profit_rate"], now,
                        c["pnl_date"], c["code"],
                    ),
                )
    except sqlite3.Error as e:
        print(f"❌ 書き込みに失敗しました: {e}")
        return 1

    print(f"\n✅ {len(plan)}件を更新しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
