"""Google Sheets → SQLite 一方向同期モジュール"""

import sqlite3
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from .stock_utils import get_currency_from_symbol, is_foreign_stock

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _to_float(v: object) -> float:
    """数値の安全な変換（カンマ除去、空→0.0）"""
    if not v and v != 0:
        return 0.0
    s = str(v).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _to_float_or_none(v: object) -> float | None:
    """数値の安全な変換（カンマ除去、空→None）"""
    if not v and v != 0:
        return None
    s = str(v).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


class SheetsSync:
    """Sheets のポートフォリオシートを SQLite の holdings / purchase_history に同期"""

    def __init__(
        self, credentials_path: str, spreadsheet_id: str, db_path: str
    ) -> None:
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        self.spreadsheet = gc.open_by_key(spreadsheet_id)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")

    def _read_portfolio_rows(self) -> list[dict]:
        """ポートフォリオシートの全行を読み取る（同一セッション内はキャッシュ）"""
        if not hasattr(self, "_portfolio_cache"):
            sheet = self.spreadsheet.worksheet("ポートフォリオ")
            self._portfolio_cache: list[dict] = sheet.get_all_records()
        return self._portfolio_cache

    @staticmethod
    def _parse_row(row: dict) -> dict | None:
        """スプレッドシートの1行をパースする。銘柄コードが空なら None を返す。

        通貨・外国株フラグは銘柄コードから自動導出する（スプレッドシートの
        該当列は読まない）。手動列との不整合による誤判定を根絶するため。
        """
        code = str(row.get("銘柄コード", "")).strip()
        if not code:
            return None

        # 銘柄コードを唯一の真実として通貨・外国株判定を導出
        currency = get_currency_from_symbol(code)
        is_foreign = 1 if is_foreign_stock(code) else 0

        return {
            "code": code,
            "name": str(row.get("銘柄名", "")),
            "acquired_date": str(row.get("取得日", "")) or None,
            "acquired_price_jpy": _to_float(row.get("取得単価（円）")),
            "acquired_price_foreign": _to_float_or_none(row.get("取得単価（外貨）")),
            "acquired_exchange_rate": _to_float_or_none(row.get("取得時為替レート")),
            "shares": _to_float(row.get("保有株数")),
            "currency": currency,
            "is_foreign": is_foreign,
            "memo": str(row.get("備考", "")) or None,
            "updated_at": str(row.get("最終更新", "")) or datetime.now().isoformat(),
        }

    def sync_holdings(self) -> int:
        """ポートフォリオシート → holdings テーブルに同期。

        同一銘柄コードの複数行を集約し、加重平均取得価額と合計株数で1行にまとめる。
        挿入件数（銘柄数）を返す。
        """
        records = self._read_portfolio_rows()

        # 銘柄コードごとにグループ化
        groups: dict[str, list[dict]] = {}
        for row in records:
            parsed = self._parse_row(row)
            if not parsed:
                continue
            groups.setdefault(parsed["code"], []).append(parsed)

        # 全削除 → 集約して挿入
        self.conn.execute("DELETE FROM holdings")

        count = 0
        for code, rows in groups.items():
            total_shares = sum(r["shares"] for r in rows)
            # 加重平均取得価額（円）= Σ(取得単価 × 株数) / 合計株数
            if total_shares > 0:
                avg_price_jpy = (
                    sum(r["acquired_price_jpy"] * r["shares"] for r in rows)
                    / total_shares
                )
            else:
                avg_price_jpy = rows[0]["acquired_price_jpy"]

            # 外貨建ての加重平均（外貨価格がある行のみ）
            foreign_rows = [r for r in rows if r["acquired_price_foreign"]]
            if foreign_rows:
                foreign_shares = sum(r["shares"] for r in foreign_rows)
                avg_price_foreign: float | None = (
                    sum(
                        r["acquired_price_foreign"] * r["shares"]  # type: ignore[operator]
                        for r in foreign_rows
                    )
                    / foreign_shares
                    if foreign_shares > 0
                    else foreign_rows[0]["acquired_price_foreign"]
                )
                avg_exchange_rate: float | None = (
                    sum(
                        r["acquired_exchange_rate"] * r["shares"]  # type: ignore[operator]
                        for r in foreign_rows
                    )
                    / foreign_shares
                    if foreign_shares > 0
                    else foreign_rows[0]["acquired_exchange_rate"]
                )
            else:
                avg_price_foreign = rows[0]["acquired_price_foreign"]
                avg_exchange_rate = rows[0]["acquired_exchange_rate"]

            # 最も古い取得日を使用
            dates = [r["acquired_date"] for r in rows if r["acquired_date"]]
            earliest_date = min(dates) if dates else None

            # 最初の行からメタ情報を取得（通貨・外国株フラグは銘柄コード由来で全行同一）
            first = rows[0]

            self.conn.execute(
                """
                INSERT INTO holdings (code, name, acquired_date, acquired_price_jpy,
                    acquired_price_foreign, acquired_exchange_rate, shares,
                    currency, is_foreign, memo, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    code,
                    first["name"],
                    earliest_date,
                    round(avg_price_jpy, 2),
                    round(avg_price_foreign, 2) if avg_price_foreign else None,
                    round(avg_exchange_rate, 4) if avg_exchange_rate else None,
                    total_shares,
                    first["currency"],
                    first["is_foreign"],
                    first["memo"],
                    first["updated_at"],
                ),
            )
            count += 1

        self.conn.commit()
        print(f"  holdings テーブルに {count} 件同期しました")
        return count

    def sync_purchase_history(self) -> int:
        """ポートフォリオシート → purchase_history テーブルに同期。

        同一銘柄コードの行を取得日順に並べ、seq（購入回）を振って保存する。
        挿入件数を返す。
        """
        records = self._read_portfolio_rows()

        # 銘柄コードごとにグループ化
        groups: dict[str, list[dict]] = {}
        for row in records:
            parsed = self._parse_row(row)
            if not parsed:
                continue
            groups.setdefault(parsed["code"], []).append(parsed)

        # 全削除 → 全挿入
        self.conn.execute("DELETE FROM purchase_history")

        count = 0
        for code, rows in groups.items():
            # 取得日でソート（空文字は末尾に）
            sorted_rows = sorted(
                rows, key=lambda r: r["acquired_date"] or "9999-99-99"
            )

            for seq, r in enumerate(sorted_rows, start=1):
                self.conn.execute(
                    """
                    INSERT INTO purchase_history
                        (code, seq, shares, price, price_foreign,
                         exchange_rate, purchased_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        code,
                        seq,
                        r["shares"],
                        r["acquired_price_jpy"],
                        r["acquired_price_foreign"],
                        r["acquired_exchange_rate"],
                        r["acquired_date"] or "",
                    ),
                )
                count += 1

        self.conn.commit()
        print(f"  purchase_history テーブルに {count} 件同期しました")
        return count

    def close(self) -> None:
        self.conn.close()
