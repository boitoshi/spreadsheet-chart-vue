"""Google Sheets → SQLite 一方向同期モジュール"""

import sqlite3
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

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
    """Sheets のポートフォリオシートを SQLite の holdings に同期"""

    def __init__(
        self, credentials_path: str, spreadsheet_id: str, db_path: str
    ) -> None:
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        self.spreadsheet = gc.open_by_key(spreadsheet_id)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")

    def sync_holdings(self) -> int:
        """ポートフォリオシート → holdings テーブルに全件同期。挿入件数を返す"""
        sheet = self.spreadsheet.worksheet("ポートフォリオ")
        records = sheet.get_all_records()

        # 全削除 → 全挿入（マスタデータなので REPLACE で十分）
        self.conn.execute("DELETE FROM holdings")

        count = 0
        for row in records:
            code = str(row.get("銘柄コード", "")).strip()
            if not code:
                continue

            # 外国株フラグの判定
            flag = str(row.get("外国株フラグ", ""))
            is_foreign = 1 if flag in ("○", "〇", "True", "true", "1") else 0

            self.conn.execute(
                """
                INSERT INTO holdings (code, name, acquired_date, acquired_price_jpy,
                    acquired_price_foreign, acquired_exchange_rate, shares,
                    currency, is_foreign, memo, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    code,
                    str(row.get("銘柄名", "")),
                    str(row.get("取得日", "")) or None,
                    _to_float(row.get("取得単価（円）")),
                    _to_float_or_none(row.get("取得単価（外貨）")),
                    _to_float_or_none(row.get("取得時為替レート")),
                    _to_float(row.get("保有株数")),
                    str(row.get("通貨", "JPY")) or "JPY",
                    is_foreign,
                    str(row.get("備考", "")) or None,
                    str(row.get("最終更新", "")) or datetime.now().isoformat(),
                ),
            )
            count += 1

        self.conn.commit()
        print(f"  holdings テーブルに {count} 件同期しました")
        return count

    def close(self) -> None:
        self.conn.close()
