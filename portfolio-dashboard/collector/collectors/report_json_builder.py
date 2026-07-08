"""月次レポート JSON 生成モジュール。

server/src/services/reportData.ts の buildReportData と同一形状・同一計算を
Python で再現する。DB 読み取りは DbWriter 経由。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .db_writer import DbWriter

# フォールバックカラー（stock_meta 未登録銘柄用）
_FALLBACK_COLORS = ["#FF6F00", "#7B1FA2"]


# ────────────────────────────────────────────────────────────
# 日付ユーティリティ
# ────────────────────────────────────────────────────────────


def _parse_pnl_date(date: str) -> tuple[int, int]:
    """"YYYY-MM-末" → (year, month) に変換する。"""
    parts = date.split("-")
    return int(parts[0]), int(parts[1])


def _parse_iso_date(date: str) -> tuple[int, int]:
    """"YYYY-MM-DD" → (year, month) に変換する。"""
    parts = date.split("-")
    return int(parts[0]), int(parts[1])


def _to_month_label(year: int, month: int) -> str:
    """(year, month) → "YYYY/M" 形式のラベルに変換する。"""
    return f"{year}/{month}"


def _prev_month(year: int, month: int) -> tuple[int, int]:
    """前月の (year, month) を返す。"""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _cmp_ym(a: tuple[int, int], b: tuple[int, int]) -> int:
    """年月の大小比較（負: a < b, 0: 同等, 正: a > b）。"""
    if a[0] != b[0]:
        return a[0] - b[0]
    return a[1] - b[1]


def _to_pnl_date(year: int, month: int) -> str:
    """(year, month) → "YYYY-MM-末" 形式の文字列に変換する。"""
    return f"{year}-{month:02d}-末"


# ────────────────────────────────────────────────────────────
# メイン関数
# ────────────────────────────────────────────────────────────


def build_report_data(db: DbWriter, target_date: str | None = None) -> dict | None:
    """月次レポートデータを構築する。

    server/src/services/reportData.ts の buildReportData と同一形状・同一計算を
    Python で再現する。

    Args:
        db: DbWriter インスタンス
        target_date: "YYYY-MM-末" 形式の対象月。省略時は monthly_pnl の最新 date を使用

    Returns:
        ReportData 相当の辞書。対象月のデータが存在しない場合は None。

        形状:
        {
            "meta": {
                "year": int,
                "month": int,
                "exchangeRate": float,
                "reportDate": "YYYY年M月末"
            },
            "stocks": [...],   # StockReportData のリスト
            "totalHistory": {
                "months": ["YYYY/M", ...],
                "assetValues": [float, ...],
                "plValues": [float, ...]
            },
            "intro": str | None,
            "summary": str | None
        }
    """
    # ── 1. 対象月の決定 ──────────────────────────────────────────
    if target_date is None:
        # monthly_pnl の最新 date を取得
        db.conn.row_factory = __import__("sqlite3").Row
        cursor = db.conn.execute(
            "SELECT date FROM monthly_pnl ORDER BY date DESC LIMIT 1"
        )
        row = cursor.fetchone()
        db.conn.row_factory = None
        if row is None:
            return None
        resolved_date: str = row["date"]
    else:
        resolved_date = target_date

    # 対象月の monthly_pnl が存在するか確認
    target_records = db.get_performance_data(*_parse_pnl_date(resolved_date))
    if not target_records:
        return None

    target_ym = _parse_pnl_date(resolved_date)
    target_year, target_month = target_ym

    # ── 2. stock_meta の取得 ──────────────────────────────────────
    meta_map = db.get_stock_meta()
    fallback_idx = 0

    # ── 3. USD/JPY レートの取得 ────────────────────────────────────
    usd_jpy = db.get_exchange_rate_for_month("USD/JPY", target_year, target_month)
    if usd_jpy is None:
        usd_jpy = 0.0

    # ── 4. 全 monthly_pnl の集計（totalHistory 用） ───────────────
    all_pnl = db.get_pnl_history_until(resolved_date)

    # 日付ごとに value / profit を集計
    total_by_date: dict[str, dict[str, float]] = {}
    for r in all_pnl:
        d = r["date"]
        if d not in total_by_date:
            total_by_date[d] = {"asset_value": 0.0, "pl": 0.0}
        total_by_date[d]["asset_value"] += r["value"]
        total_by_date[d]["pl"] += r["profit"]

    sorted_dates = sorted(total_by_date.keys())
    total_history = {
        "months": [
            _to_month_label(*_parse_pnl_date(d)) for d in sorted_dates
        ],
        "assetValues": [total_by_date[d]["asset_value"] for d in sorted_dates],
        "plValues": [total_by_date[d]["pl"] for d in sorted_dates],
    }

    # ── 5. 各銘柄の詳細データ構築 ────────────────────────────────
    stocks: list[dict] = []

    for pnl_row in target_records:
        code: str = pnl_row["code"]
        is_foreign = pnl_row["currency"] != "JPY"
        meta = meta_map.get(code)

        # 色の決定（stock_meta 未登録はフォールバック）
        if meta and meta.get("color"):
            color: str = meta["color"]
        else:
            color = _FALLBACK_COLORS[fallback_idx % len(_FALLBACK_COLORS)]
            fallback_idx += 1

        market: str = meta["market"] if meta else ""

        # ── 5a. 全期間の monthly_pnl 履歴（保有開始月〜対象月） ────
        purchases = db.get_purchase_history(code)

        # 保有開始月を特定（最古の purchased_at から）
        if purchases:
            first_purchase_ym = _parse_iso_date(purchases[0]["purchased_at"])
        else:
            first_purchase_ym = target_ym

        # monthly_pnl を保有開始月から対象月まで取得
        # get_pnl_history_until は resolved_date 以下全件のため、コードで絞り込む
        db.conn.row_factory = __import__("sqlite3").Row
        cursor = db.conn.execute(
            """
            SELECT * FROM monthly_pnl
            WHERE code = ? AND date <= ?
            ORDER BY date ASC
            """,
            (code, resolved_date),
        )
        pnl_history_rows = cursor.fetchall()
        db.conn.row_factory = None

        # 保有開始月より前のレコードを除外
        pnl_history = [
            dict(r)
            for r in pnl_history_rows
            if _cmp_ym(_parse_pnl_date(r["date"]), first_purchase_ym) >= 0
        ]

        month_labels = [
            _to_month_label(*_parse_pnl_date(r["date"])) for r in pnl_history
        ]

        # ネイティブ通貨の月末価格配列
        price_history = [
            float(
                r["current_price_foreign"]
                if is_foreign and r["current_price_foreign"] is not None
                else r["current_price"]
            )
            for r in pnl_history
        ]

        # ── 5b. 移動平均取得単価の計算（stepped line） ──────────────
        # 購入履歴を purchased_at 昇順 → seq 昇順でソート
        sorted_purchases = sorted(
            purchases,
            key=lambda p: (_parse_iso_date(p["purchased_at"]), p["seq"]),
        )

        cum_cost = 0.0
        cum_shares = 0.0
        purchase_idx = 0
        acquired_avg_history: list[float] = []

        for r in pnl_history:
            month_ym = _parse_pnl_date(r["date"])

            # この月までの購入を累積
            while purchase_idx < len(sorted_purchases):
                p = sorted_purchases[purchase_idx]
                p_ym = _parse_iso_date(p["purchased_at"])
                if _cmp_ym(p_ym, month_ym) <= 0:
                    # USD 銘柄は price_foreign、JPY は price を使用
                    native_price = (
                        float(p["price_foreign"] or 0.0)
                        if is_foreign
                        else float(p["price"])
                    )
                    cum_cost += native_price * float(p["shares"])
                    cum_shares += float(p["shares"])
                    purchase_idx += 1
                else:
                    break

            acquired_avg_history.append(
                cum_cost / cum_shares if cum_shares > 0 else 0.0
            )

        # 対象月末時点の移動平均取得単価（acquiredAvgHistory の最終値）
        acquired_price = acquired_avg_history[-1] if acquired_avg_history else 0.0

        # ── 5c. 取引リスト（monthLabels のインデックス付き） ──────
        transactions: list[dict] = []
        for p in sorted_purchases:
            p_ym = _parse_iso_date(p["purchased_at"])
            if _cmp_ym(p_ym, target_ym) > 0:
                # 対象月より後の購入は除外
                continue

            purchase_label = _to_month_label(*p_ym)
            if purchase_label in month_labels:
                month_idx = month_labels.index(purchase_label)
            else:
                # 該当月が month_labels にない場合→翌月以降の最初の月を使用
                month_idx = -1
                for i, label in enumerate(month_labels):
                    lbl_parts = label.split("/")
                    lbl_ym = (int(lbl_parts[0]), int(lbl_parts[1]))
                    if _cmp_ym(lbl_ym, p_ym) >= 0:
                        month_idx = i
                        break
                if month_idx == -1:
                    continue

            transactions.append(
                {
                    "month": month_idx,
                    "action": "buy",
                    "quantity": int(p["shares"]),
                    "price": (
                        float(p["price_foreign"] or 0.0)
                        if is_foreign
                        else float(p["price"])
                    ),
                }
            )

        # ── 5d. 前月のネイティブ価格 ────────────────────────────
        prev_ym = _prev_month(target_year, target_month)
        prev_pnl_date = _to_pnl_date(*prev_ym)

        db.conn.row_factory = __import__("sqlite3").Row
        cursor = db.conn.execute(
            "SELECT * FROM monthly_pnl WHERE code = ? AND date = ? LIMIT 1",
            (code, prev_pnl_date),
        )
        prev_row = cursor.fetchone()
        db.conn.row_factory = None

        if prev_row:
            previous_month_price: float | None = float(
                prev_row["current_price_foreign"]
                if is_foreign and prev_row["current_price_foreign"] is not None
                else prev_row["current_price"]
            )
        else:
            previous_month_price = None

        # ── 5e. monthly_prices の月間変動率 ──────────────────────
        prefix = f"{target_year}-{target_month:02d}"
        db.conn.row_factory = __import__("sqlite3").Row
        cursor = db.conn.execute(
            """
            SELECT change_rate FROM monthly_prices
            WHERE code = ? AND date LIKE ?
            LIMIT 1
            """,
            (code, f"{prefix}%"),
        )
        price_row = cursor.fetchone()
        db.conn.row_factory = None
        monthly_change_rate: float | None = (
            float(price_row["change_rate"])
            if price_row and price_row["change_rate"] is not None
            else None
        )

        # ── 5f. 保有株数（purchase_history から集計） ──────────────
        # 対象月の翌月1日より前の購入を合計
        if target_month < 12:
            next_month_first_day = (
                f"{target_year}-{target_month + 1:02d}-01"
            )
        else:
            next_month_first_day = f"{target_year + 1}-01-01"

        quantity = sum(
            int(p["shares"])
            for p in sorted_purchases
            if p["purchased_at"] < next_month_first_day
        )

        # ── 5g. AI コメント ───────────────────────────────────────
        ai_comments_map = db.get_ai_comments(resolved_date)
        comment = ai_comments_map.get((code, "stock"), None)

        stocks.append(
            {
                "code": code,
                "name": pnl_row["name"],
                "ticker": code,
                "market": market,
                "currency": "USD" if is_foreign else "JPY",
                "quantity": quantity,
                "currentPrice": float(
                    pnl_row["current_price_foreign"]
                    if is_foreign and pnl_row["current_price_foreign"] is not None
                    else pnl_row["current_price"]
                ),
                "previousMonthPrice": previous_month_price,
                "monthlyChangeRate": monthly_change_rate,
                "color": color,
                "acquiredPrice": acquired_price,
                "priceHistory": price_history,
                "acquiredAvgHistory": acquired_avg_history,
                "monthLabels": month_labels,
                "transactions": transactions,
                "comment": comment,
                "value": float(pnl_row["value"]),
                "profit": float(pnl_row["profit"]),
                "profitRate": float(pnl_row["profit_rate"]),
            }
        )

    # ── 6. AI コメント（intro / summary） ────────────────────────
    ai_comments_map = db.get_ai_comments(resolved_date)
    intro = ai_comments_map.get(("", "intro"), None)
    summary = ai_comments_map.get(("", "summary"), None)

    return {
        "meta": {
            "year": target_year,
            "month": target_month,
            "exchangeRate": usd_jpy,
            "reportDate": f"{target_year}年{target_month}月末",
        },
        "stocks": stocks,
        "totalHistory": total_history,
        "intro": intro,
        "summary": summary,
    }
