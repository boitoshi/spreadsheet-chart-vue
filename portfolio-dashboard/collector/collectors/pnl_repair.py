"""monthly_pnl テーブルの取得系カラムを purchase_history からバックフィルする。

過去の移行ミスにより、monthly_pnl の一部の行が「最後の買付行のみ」の
株数・取得単価になっている（例: 2024-12-末 NVDA が shares=1、正しくは 4）。
このモジュールは purchase_history から月末時点の累積株数・加重平均取得単価を
再計算し、shares / cost / acquired_price 系のみを UPDATE する。

current_price / current_price_foreign / current_exchange_rate / currency /
name は保存済みの正しい市場データであり、絶対に変更しない。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .purchase_math import cumulative_position
from .stock_utils import is_foreign_stock

if TYPE_CHECKING:
    from .db_writer import DbWriter

# 変更判定の許容誤差（これ以下の差は丸め誤差とみなし「変更なし」扱いにする）
_DIFF_THRESHOLD = 0.005

# compute_row_update が再計算する 8 フィールド（UPDATE 対象・変更判定対象）
_RECOMPUTED_FIELDS = (
    "shares",
    "cost",
    "acquired_price",
    "acquired_price_foreign",
    "acquired_exchange_rate",
    "value",
    "profit",
    "profit_rate",
)


def _parse_pnl_date(date_str: str) -> tuple[int, int]:
    """"YYYY-MM-末" 形式の日付文字列から (year, month) を取り出す。"""
    year_str, month_str, _ = date_str.split("-")
    return int(year_str), int(month_str)


def compute_row_update(
    pnl_row: dict, purchases: list[dict]
) -> tuple[dict, list[tuple[str, float, float]]] | None:
    """monthly_pnl の1行分の UPDATE 内容を計算する（純粋関数・DB 非依存）。

    Args:
        pnl_row: monthly_pnl の行（dict）。date は "YYYY-MM-末" 形式。
        purchases: 同一銘柄の購入履歴（dict のリスト）。

    Returns:
        (UPDATE 用 dict, 変更リスト) のタプル。変更リストは
        [(フィールド名, 変更前, 変更後), ...] の形で、値に変化がなければ空。
        買付前の月（累積株数 0）または購入履歴が空の場合は None。
    """
    if not purchases:
        return None

    code = pnl_row["code"]
    date = pnl_row["date"]
    year, month = _parse_pnl_date(date)
    is_foreign = is_foreign_stock(code)

    pos = cumulative_position(purchases, year, month, is_foreign=is_foreign)
    if pos.shares == 0:
        return None

    shares = pos.shares
    cost = round(pos.cost_jpy, 2)
    acquired_price = round(pos.avg_price_jpy, 2)
    acquired_price_foreign = round(pos.avg_price_native, 2)
    acquired_exchange_rate = round(pos.avg_exchange_rate, 4)

    current_price = pnl_row["current_price"]
    value = round(current_price * shares, 2)
    profit = round(value - cost, 2)
    profit_rate = round(profit / cost * 100, 2) if cost > 0 else 0.0

    new_values = {
        "shares": shares,
        "cost": cost,
        "acquired_price": acquired_price,
        "acquired_price_foreign": acquired_price_foreign,
        "acquired_exchange_rate": acquired_exchange_rate,
        "value": value,
        "profit": profit,
        "profit_rate": profit_rate,
    }

    changes: list[tuple[str, float, float]] = []
    for field in _RECOMPUTED_FIELDS:
        after = new_values[field]
        before = pnl_row.get(field)
        before = 0.0 if before is None else before
        if abs(before - after) > _DIFF_THRESHOLD:
            changes.append((field, before, after))

    update = {
        "date": date,
        "code": code,
        **new_values,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return update, changes


def repair_monthly_pnl(
    db: DbWriter,
    dry_run: bool = False,
    target_months: list[tuple[int, int]] | None = None,
    verbose: bool = True,
) -> dict:
    """monthly_pnl の取得系カラムを purchase_history 基準でバックフィルする。

    Args:
        db: DbWriter インスタンス。
        dry_run: True の場合は再計算・差分表示のみ行い、DB は更新しない。
        target_months: 対象を絞る (year, month) のリスト。None なら全期間。
        verbose: True なら詳細ログを表示する。False なら更新件数のみ 1 行表示
            （変更 0 行なら何も出力しない）。

    Returns:
        {"total": 対象行数, "changed": 変更行数, "unchanged": 変更なし行数,
         "skipped": スキップ行数} の集計 dict。
    """
    all_rows = db.get_all_pnl_data()
    if target_months is not None:
        target_set = set(target_months)
        rows = [r for r in all_rows if _parse_pnl_date(r["date"]) in target_set]
    else:
        rows = all_rows

    if verbose:
        mode_label = "dry-run" if dry_run else "実行"
        codes = sorted({r["code"] for r in rows})
        dates = sorted({r["date"] for r in rows})
        period = f"{dates[0]} 〜 {dates[-1]}" if dates else "該当なし"
        print(f"\n=== monthly_pnl バックフィル（{mode_label}） ===")
        print(f"  対象: {len(rows)}行 / {len(codes)}銘柄 / 期間: {period}")

    purchase_cache: dict[str, list[dict]] = {}
    updates: list[dict] = []
    changed = 0
    unchanged = 0
    skipped = 0

    for row in rows:
        code = row["code"]
        if code not in purchase_cache:
            purchase_cache[code] = db.get_purchase_history(code)
        purchases = purchase_cache[code]

        result = compute_row_update(row, purchases)
        if result is None:
            skipped += 1
            if verbose:
                print(
                    f"  ⚠ [{row['date']}] {code}: "
                    "買付前の月または購入履歴なしのためスキップ"
                )
            continue

        update, changes = result
        if changes:
            changed += 1
            updates.append(update)
            if verbose:
                print(f"  ● [{row['date']}] {code}")
                for field, before, after in changes:
                    print(f"      {field}: {before:.4f} → {after:.4f}")
        else:
            unchanged += 1

    if verbose:
        print(
            f"\n  サマリー: 対象 {len(rows)}行 / 変更 {changed}行 / "
            f"変更なし {unchanged}行 / スキップ {skipped}行"
        )
        if dry_run:
            print("  ※ dry-run のため DB は変更していません")
    elif changed:
        print(f"  monthly_pnl 補正: {changed}行更新")

    if not dry_run and updates:
        db.update_monthly_pnl_acquisition(updates)

    return {
        "total": len(rows),
        "changed": changed,
        "unchanged": unchanged,
        "skipped": skipped,
    }
