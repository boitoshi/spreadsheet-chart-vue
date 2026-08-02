"""月次レポート JSON 生成モジュール。

server/src/services/reportData.ts の buildReportData と同一形状・同一計算を
Python で再現する。DB 読み取りは DbWriter 経由。
"""

from __future__ import annotations

import itertools
from datetime import date, timedelta
from typing import TYPE_CHECKING

import yfinance as yf

if TYPE_CHECKING:
    from .db_writer import DbWriter

# フォールバックカラー（stock_meta 未登録銘柄用）
_FALLBACK_COLORS = ["#FF6F00", "#7B1FA2"]

# priceSeries 間引きの閾値: 対象月末からこの日数以内は日次のまま残し、
# それより古い期間は週次（各ISO週の最終営業日のみ）に間引く
_PRICE_SERIES_DAILY_WINDOW_DAYS = 365


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


def _date_from_iso(iso_str: str) -> date:
    """"YYYY-MM-DD" 文字列を date オブジェクトに変換する。"""
    y, m, d = iso_str.split("-")
    return date(int(y), int(m), int(d))


def _month_end_date(year: int, month: int) -> str:
    """(year, month) → その月の最終日を "YYYY-MM-DD" 形式で返す。"""
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    return (next_month_first - timedelta(days=1)).strftime("%Y-%m-%d")


# ────────────────────────────────────────────────────────────
# priceSeries / purchaseHistory 構築ユーティリティ
# （ブログ埋め込み専用フィールド。server/src/services/reportData.ts には
#  対応フィールドが無い。dashboard 側の形状には影響しないため、この
#  モジュール内だけで完結させる）
# ────────────────────────────────────────────────────────────


def _thin_price_series(
    dates: list[str], values: list[float]
) -> tuple[list[str], list[float]]:
    """日次系列を間引く。

    対象月末（dates の最終要素）から遡って _PRICE_SERIES_DAILY_WINDOW_DAYS 日
    以内は日次のまま残し、それより古い期間は各 ISO 週の最終営業日の値だけを
    残す（週次化）。dates の先頭要素（最初の購入日以降で最初に取れた営業日）
    は間引きで落ちても必ず戻す。

    Args:
        dates: "YYYY-MM-DD" 昇順の日付リスト
        values: dates と同じ長さの値リスト

    Returns:
        間引き後の (dates, values)。dates が空の場合は ([], [])。
    """
    if not dates:
        return [], []

    last_date = _date_from_iso(dates[-1])
    cutoff = last_date - timedelta(days=_PRICE_SERIES_DAILY_WINDOW_DAYS)

    # cutoff 以降（日次のまま残す区間）の開始位置を探す
    split_idx = len(dates)
    for i, d in enumerate(dates):
        if _date_from_iso(d) >= cutoff:
            split_idx = i
            break

    old_pairs = list(zip(dates[:split_idx], values[:split_idx], strict=True))
    recent_dates, recent_values = dates[split_idx:], values[split_idx:]

    # 古い区間: ISO 週（年, 週番号）でグループ化し、各週最後の営業日だけ残す
    thinned_dates: list[str] = []
    thinned_values: list[float] = []
    for _, group in itertools.groupby(
        old_pairs, key=lambda pair: _date_from_iso(pair[0]).isocalendar()[:2]
    ):
        last_pair = list(group)[-1]
        thinned_dates.append(last_pair[0])
        thinned_values.append(last_pair[1])

    thinned_dates.extend(recent_dates)
    thinned_values.extend(recent_values)

    # 最初の購入日以降で最初に取れた営業日の点は週次間引きで落ちる場合が
    # あるため、必ず先頭に戻す
    if thinned_dates[0] != dates[0]:
        thinned_dates.insert(0, dates[0])
        thinned_values.insert(0, values[0])

    return thinned_dates, thinned_values


def _acquired_avg_series_daily(
    dates: list[str], purchases_by_date: list[dict], is_foreign: bool
) -> list[float | None]:
    """指定した日付リストの各時点における加重平均取得単価（ネイティブ通貨）を返す。

    purchases_by_date は purchased_at 昇順（seq 昇順）に整列済みであること
    （report_json_builder.build_report_data 内の sorted_purchases を渡す想定）。
    各 date 時点までに成立した購入だけを累積する。最初の購入日より前の日付は
    None（このモジュールの呼び出し元では dates の先頭が最初の購入日以降に
    限られるため実際には発生しない想定だが、防御的に扱う）。

    Args:
        dates: "YYYY-MM-DD" 昇順の日付リスト
        purchases_by_date: purchased_at 昇順に整列済みの購入履歴
        is_foreign: 外国株かどうか（True なら price_foreign を使用）

    Returns:
        dates と同じ長さの加重平均取得単価リスト（未購入時点は None）
    """
    cum_cost = 0.0
    cum_shares = 0.0
    idx = 0
    result: list[float | None] = []

    for d in dates:
        while idx < len(purchases_by_date):
            p = purchases_by_date[idx]
            if p["purchased_at"] > d:
                break
            native_price = (
                float(p["price_foreign"] or 0.0) if is_foreign else float(p["price"])
            )
            cum_cost += native_price * float(p["shares"])
            cum_shares += float(p["shares"])
            idx += 1

        result.append(cum_cost / cum_shares if cum_shares > 0 else None)

    return result


def _fetch_price_series(
    symbol: str,
    is_foreign: bool,
    first_purchase_date: str,
    month_end_date: str,
    purchases_by_date: list[dict],
) -> dict | None:
    """priceSeries（株価・加重平均取得単価の日次/週次系列）を構築する。

    yfinance から最初の購入日〜対象月末の日次終値（ネイティブ通貨）を取得し、
    _thin_price_series で間引いたうえで、各時点の加重平均取得単価を添える。
    取得失敗（yfinance が空を返す・例外）時は None を返し、警告を出力する
    （呼び出し元はこれを許容し、他の処理を止めない）。

    Args:
        symbol: 銘柄コード（yfinance のティッカー、例: "7974.T", "NVDA"）
        is_foreign: 外国株かどうか
        first_purchase_date: 最初の購入日（"YYYY-MM-DD"）
        month_end_date: 対象月の月末日（"YYYY-MM-DD"）
        purchases_by_date: purchased_at 昇順に整列済みの購入履歴

    Returns:
        {"labels": [...], "prices": [...], "acquired": [...]} の辞書。
        取得失敗時は None。
    """
    try:
        # auto_adjust=False: 既存DBの値は未調整終値のため、yfinanceの
        # 既定変更（調整後値）が混入しないよう明示する（stock_collector.py と同じ理由）
        end_exclusive = _date_from_iso(month_end_date) + timedelta(days=1)
        raw = yf.Ticker(symbol).history(
            start=first_purchase_date,
            end=end_exclusive.strftime("%Y-%m-%d"),
            auto_adjust=False,
        )
    except Exception as e:
        print(f"⚠️ priceSeries 取得エラー（{symbol}）: {e}")
        return None

    if raw.empty:
        print(f"⚠️ priceSeries: {symbol} の日次データが取得できませんでした")
        return None

    dates: list[str] = []
    closes: list[float] = []
    for idx, close in zip(raw.index, raw["Close"], strict=True):
        d = idx.strftime("%Y-%m-%d")
        if d > month_end_date:
            # 対象月末より後のデータは含めない（過去月の記事に未来の値が出ないように）
            continue
        dates.append(d)
        closes.append(float(close))

    if not dates:
        print(f"⚠️ priceSeries: {symbol} に対象範囲内の日次データがありません")
        return None

    thinned_dates, thinned_prices = _thin_price_series(dates, closes)
    acquired = _acquired_avg_series_daily(thinned_dates, purchases_by_date, is_foreign)

    return {
        "labels": thinned_dates,
        "prices": thinned_prices,
        "acquired": acquired,
    }


def _build_purchase_history(
    purchases: list[dict], is_foreign: bool, target_ym: tuple[int, int]
) -> list[dict]:
    """purchase_history テーブルの生データを埋め込み用の購入履歴リストに変換する。

    既存の transactions（チャートの買付マーカー用。month インデックス + 数量 +
    価格のみ）とは別に持たせるフィールド。埋め込みHTML側の「買い増し記録」表に
    必要な購入日・為替レートを持つ。対象月の月末までに成立した購入のみを含む
    （未来の買付が過去月の記事に出ないようにする）。

    Args:
        purchases: db.get_purchase_history(code) の戻り値（seq 昇順）
        is_foreign: 外国株かどうか
        target_ym: 対象年月。この月以前（同月含む）の購入のみ含む

    Returns:
        {"seq", "shares", "price", "exchangeRate"（外国株のみ）, "purchasedAt"}
        の辞書のリスト（seq 昇順）
    """
    result: list[dict] = []
    for p in purchases:
        p_ym = _parse_iso_date(p["purchased_at"])
        if _cmp_ym(p_ym, target_ym) > 0:
            continue

        entry: dict = {
            "seq": int(p["seq"]),
            "shares": float(p["shares"]),
            "price": (
                float(p["price_foreign"] or 0.0) if is_foreign else float(p["price"])
            ),
        }
        if is_foreign:
            entry["exchangeRate"] = (
                float(p["exchange_rate"]) if p["exchange_rate"] is not None else None
            )
        entry["purchasedAt"] = p["purchased_at"]
        result.append(entry)

    return result


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
                "reportDate": "YYYY年M月末",
                "purchasesThisMonth": [
                    {"name": str, "shares": float, "price": float,
                     "currency": "JPY" | "USD", "purchasedAt": "YYYY-MM-DD"},
                    ...
                ]  # 対象月に成立した買い増しのみ。無ければ空リスト
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
    # priceSeries 取得範囲の終端（対象月の月末日）。全銘柄共通のため一度だけ計算
    target_month_end_date = _month_end_date(target_year, target_month)

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
    # 対象月に成立した買い増しだけを集める（ブログ埋め込み冒頭の「今月の買い増し」用）
    purchases_this_month: list[dict] = []

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

        # 対象月ちょうどの購入だけ拾って purchasesThisMonth に積む
        for p in purchases:
            if _parse_iso_date(p["purchased_at"]) == target_ym:
                purchases_this_month.append(
                    {
                        "name": pnl_row["name"],
                        "shares": float(p["shares"]),
                        "price": (
                            float(p["price_foreign"] or 0.0)
                            if is_foreign
                            else float(p["price"])
                        ),
                        "currency": "USD" if is_foreign else "JPY",
                        "purchasedAt": p["purchased_at"],
                    }
                )

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

        # ── 5b-2. priceSeries の構築（ブログ埋め込み専用フィールド） ──────
        # dashboard 側 reportData.ts には対応フィールドが無い。埋め込みHTML の
        # 期間切替チャート（3ヶ月/6ヶ月/1年/設定来）用に、このモジュールだけで
        # 追加する（既存フィールドの priceHistory/acquiredAvgHistory は月次の
        # ままで変更しない）
        price_series: dict | None = None
        if sorted_purchases:
            price_series = _fetch_price_series(
                code,
                is_foreign,
                sorted_purchases[0]["purchased_at"],
                target_month_end_date,
                sorted_purchases,
            )

        # ── 5b-3. purchaseHistory の構築（ブログ埋め込み専用フィールド） ────
        # 買い増し記録の表に必要な購入日・為替レートを持たせる。既存の
        # transactions（チャートの買付マーカー用）はそのまま残す
        purchase_history = _build_purchase_history(purchases, is_foreign, target_ym)

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

        # ── 5d-2. 前月比（円建て） ──────────────────────────────
        # current_price は通貨に関わらず円建て（外国株も円換算済み）のため、
        # 円建て同士で比較すれば為替変動を含んだ「実際の評価額の前月比」になる
        if prev_row and prev_row["current_price"] is not None:
            prev_yen_price = float(prev_row["current_price"])
            current_yen_price = float(pnl_row["current_price"])
            prev_month_change_rate: float | None = (
                (current_yen_price / prev_yen_price - 1) * 100
                if prev_yen_price != 0
                else None
            )
        else:
            prev_month_change_rate = None

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
                "prevMonthChangeRate": prev_month_change_rate,
                "color": color,
                "acquiredPrice": acquired_price,
                "priceHistory": price_history,
                "acquiredAvgHistory": acquired_avg_history,
                "monthLabels": month_labels,
                "transactions": transactions,
                "purchaseHistory": purchase_history,
                "priceSeries": price_series,
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

    purchases_this_month.sort(key=lambda p: p["purchasedAt"])

    return {
        "meta": {
            "year": target_year,
            "month": target_month,
            "exchangeRate": usd_jpy,
            "reportDate": f"{target_year}年{target_month}月末",
            "purchasesThisMonth": purchases_this_month,
        },
        "stocks": stocks,
        "totalHistory": total_history,
        "intro": intro,
        "summary": summary,
    }
