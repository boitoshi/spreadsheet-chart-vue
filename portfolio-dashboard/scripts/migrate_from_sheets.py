"""
Google Sheets → SQLite 移行スクリプト
既存の 5 シートからデータを読み取り、SQLite に UPSERT する

使い方:
  cd portfolio-dashboard
  python scripts/migrate_from_sheets.py
"""

import os
import re
import sqlite3
import sys
from pathlib import Path

# スクリプトのディレクトリから相対パスを解決
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent  # portfolio-dashboard/
REPO_ROOT = PROJECT_DIR.parent   # spreadsheet-chart-vue/

# デフォルトパス
DEFAULT_CREDENTIALS = REPO_ROOT / "data-collector" / "config" / "my-service-account.json"
DEFAULT_ENV_FILE = REPO_ROOT / "data-collector" / ".env"
DEFAULT_DB_PATH = PROJECT_DIR / "server" / "data" / "portfolio.db"
MIGRATION_SQL = PROJECT_DIR / "server" / "drizzle" / "migrations" / "0000_wise_morgan_stark.sql"

# shared/sheets_config.py を参照
sys.path.insert(0, str(REPO_ROOT))
from shared.sheets_config import SHEET_NAMES, HEADERS  # noqa: E402


# ---------------------------------------------------------------------------
# 環境変数読み込み（python-dotenv があれば使う、なければ手動パース）
# ---------------------------------------------------------------------------

def load_env_file(env_path: Path) -> dict[str, str]:
    """シンプルな .env パーサー（python-dotenv の代替）"""
    result: dict[str, str] = {}
    if not env_path.exists():
        return result
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
    return result


try:
    from dotenv import load_dotenv
    load_dotenv(DEFAULT_ENV_FILE)
except ImportError:
    env_vars = load_env_file(DEFAULT_ENV_FILE)
    for k, v in env_vars.items():
        os.environ.setdefault(k, v)


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def to_float(value: object, default: float | None = None) -> float | None:
    """カンマ除去・空文字対応の安全な float 変換"""
    if value is None or value == "":
        return default
    s = str(value).replace(",", "").strip()
    if s == "":
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def to_float_required(value: object) -> float:
    """必須列用（変換失敗時は 0.0）"""
    result = to_float(value, default=0.0)
    return result if result is not None else 0.0


def to_bool_int(value: object) -> int:
    """外国株フラグ変換: ○/〇/True/true/1 → 1, それ以外 → 0"""
    s = str(value).strip()
    # U+25CB（○）と U+3007（〇）の両方に対応
    if s in ("\u25cb", "\u3007", "True", "true", "1", "yes", "Yes"):
        return 1
    return 0


def skip_empty_row(row: dict, key_col: str) -> bool:
    """キー列が空の行はスキップ"""
    return not str(row.get(key_col, "")).strip()


# ---------------------------------------------------------------------------
# Google Sheets 認証
# ---------------------------------------------------------------------------

def get_spreadsheet():
    """gspread でスプレッドシートを開く"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as e:
        print(f"エラー: 必要なライブラリが見つかりません: {e}")
        print("  pip install gspread google-auth")
        sys.exit(1)

    credentials_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS", str(DEFAULT_CREDENTIALS)
    )
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not credentials_path or not Path(credentials_path).exists():
        print(f"エラー: 認証ファイルが見つかりません: {credentials_path}")
        sys.exit(1)

    if not spreadsheet_id:
        print("エラー: SPREADSHEET_ID が設定されていません")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    client = gspread.authorize(creds)
    print(f"認証成功: {credentials_path}")
    return client.open_by_key(spreadsheet_id)


# ---------------------------------------------------------------------------
# SQLite 初期化
# ---------------------------------------------------------------------------

def init_db(db_path: Path) -> sqlite3.Connection:
    """DB ファイル作成 + マイグレーション SQL 実行"""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if MIGRATION_SQL.exists():
        sql_text = MIGRATION_SQL.read_text(encoding="utf-8")
        # Drizzle の区切り文字 `--> statement-breakpoint` を除去して実行
        statements = re.split(r"--> statement-breakpoint", sql_text)
        with conn:
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    try:
                        conn.execute(stmt)
                    except sqlite3.OperationalError as e:
                        # テーブル/インデックスが既に存在する場合は無視
                        if "already exists" not in str(e):
                            raise
        print(f"マイグレーション完了: {MIGRATION_SQL}")
    else:
        print(f"警告: マイグレーションファイルが見つかりません: {MIGRATION_SQL}")

    return conn


# ---------------------------------------------------------------------------
# 各シートの移行処理
# ---------------------------------------------------------------------------

def migrate_holdings(conn: sqlite3.Connection, sheet) -> int:
    """ポートフォリオシート → holdings テーブル"""
    rows = sheet.get_all_records(expected_headers=HEADERS["PORTFOLIO"])
    count = 0
    with conn:
        for row in rows:
            if skip_empty_row(row, "銘柄コード"):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO holdings
                    (code, name, acquired_date, acquired_price_jpy,
                     acquired_price_foreign, acquired_exchange_rate,
                     shares, currency, is_foreign, memo, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["銘柄コード"]).strip(),
                    str(row["銘柄名"]).strip(),
                    str(row["取得日"]).strip() or None,
                    to_float_required(row["取得単価（円）"]),
                    to_float(row["取得単価（外貨）"]),
                    to_float(row["取得時為替レート"]),
                    to_float_required(row["保有株数"]),
                    str(row["通貨"]).strip() or "JPY",
                    to_bool_int(row["外国株フラグ"]),
                    str(row["備考"]).strip() or None,
                    str(row["最終更新"]).strip() or None,
                ),
            )
            count += 1
    return count


def migrate_monthly_prices(conn: sqlite3.Connection, sheet) -> int:
    """データ記録シート → monthly_prices テーブル"""
    rows = sheet.get_all_records(expected_headers=HEADERS["DATA_RECORD"])
    count = 0
    with conn:
        for row in rows:
            if skip_empty_row(row, "銘柄コード"):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO monthly_prices
                    (date, code, price_jpy, high, low, average,
                     change_rate, avg_volume, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["月末日付"]).strip(),
                    str(row["銘柄コード"]).strip(),
                    to_float_required(row["月末価格（円）"]),
                    to_float(row["最高値"]),
                    to_float(row["最安値"]),
                    to_float(row["平均価格"]),
                    to_float(row["月間変動率(%)"]),
                    to_float(row["平均出来高"]),
                    str(row["取得日時"]).strip() or None,
                ),
            )
            count += 1
    return count


def migrate_monthly_pnl(conn: sqlite3.Connection, sheet) -> int:
    """損益レポートシート → monthly_pnl テーブル"""
    rows = sheet.get_all_records(expected_headers=HEADERS["PERFORMANCE"])
    count = 0
    with conn:
        for row in rows:
            if skip_empty_row(row, "銘柄コード"):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO monthly_pnl
                    (date, code, name, acquired_price, current_price,
                     shares, cost, value, profit, profit_rate, currency,
                     acquired_price_foreign, current_price_foreign,
                     acquired_exchange_rate, current_exchange_rate, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["日付"]).strip(),
                    str(row["銘柄コード"]).strip(),
                    str(row["銘柄名"]).strip(),
                    to_float_required(row["取得単価"]),
                    to_float_required(row["月末価格"]),
                    to_float_required(row["保有株数"]),
                    to_float_required(row["取得額"]),
                    to_float_required(row["評価額"]),
                    to_float_required(row["損益"]),
                    to_float_required(row["損益率(%)"]),
                    str(row["通貨"]).strip() or "JPY",
                    to_float(row["取得単価（外貨）"]),
                    to_float(row["月末価格（外貨）"]),
                    to_float(row["取得時為替レート"]),
                    to_float(row["現在為替レート"]),
                    str(row["更新日時"]).strip() or None,
                ),
            )
            count += 1
    return count


def migrate_exchange_rates(conn: sqlite3.Connection, sheet) -> int:
    """為替レートシート → exchange_rates テーブル"""
    rows = sheet.get_all_records(expected_headers=HEADERS["CURRENCY"])
    count = 0
    with conn:
        for row in rows:
            if skip_empty_row(row, "通貨ペア"):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO exchange_rates
                    (date, pair, rate, prev_rate, change_rate, high, low, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["取得日"]).strip(),
                    str(row["通貨ペア"]).strip(),
                    to_float_required(row["レート"]),
                    to_float(row["前回レート"]),
                    to_float(row["変動率(%)"]),
                    to_float(row["最高値"]),
                    to_float(row["最安値"]),
                    str(row["更新日時"]).strip() or None,
                ),
            )
            count += 1
    return count


def migrate_dividends(conn: sqlite3.Connection, sheet) -> int:
    """配当・分配金シート → dividends テーブル"""
    rows = sheet.get_all_records(expected_headers=HEADERS["DIVIDEND"])
    count = 0
    with conn:
        for row in rows:
            if skip_empty_row(row, "銘柄コード"):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO dividends
                    (date, code, name, dividend_foreign, shares,
                     total_foreign, currency, exchange_rate, total_jpy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["受取日"]).strip(),
                    str(row["銘柄コード"]).strip(),
                    str(row["銘柄名"]).strip(),
                    to_float(row["1株配当（外貨）"]),
                    to_float_required(row["保有株数"]),
                    to_float(row["配当合計（外貨）"]),
                    str(row["通貨"]).strip() or "JPY",
                    to_float(row["為替レート"]),
                    to_float_required(row["配当合計（円）"]),
                ),
            )
            count += 1
    return count


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main() -> None:
    db_path = Path(os.environ.get("SQLITE_DB_PATH", str(DEFAULT_DB_PATH)))
    print(f"移行先 DB: {db_path}")

    # DB 初期化
    conn = init_db(db_path)

    # Sheets 接続
    print("\nGoogle Sheets に接続中...")
    spreadsheet = get_spreadsheet()
    print(f"スプレッドシート: {spreadsheet.title}")

    results: dict[str, int] = {}

    # holdings
    print(f"\n[1/5] {SHEET_NAMES['PORTFOLIO']} → holdings ...")
    ws = spreadsheet.worksheet(SHEET_NAMES["PORTFOLIO"])
    results["holdings"] = migrate_holdings(conn, ws)

    # monthly_prices
    print(f"[2/5] {SHEET_NAMES['DATA_RECORD']} → monthly_prices ...")
    ws = spreadsheet.worksheet(SHEET_NAMES["DATA_RECORD"])
    results["monthly_prices"] = migrate_monthly_prices(conn, ws)

    # monthly_pnl
    print(f"[3/5] {SHEET_NAMES['PERFORMANCE']} → monthly_pnl ...")
    ws = spreadsheet.worksheet(SHEET_NAMES["PERFORMANCE"])
    results["monthly_pnl"] = migrate_monthly_pnl(conn, ws)

    # exchange_rates
    print(f"[4/5] {SHEET_NAMES['CURRENCY']} → exchange_rates ...")
    ws = spreadsheet.worksheet(SHEET_NAMES["CURRENCY"])
    results["exchange_rates"] = migrate_exchange_rates(conn, ws)

    # dividends
    print(f"[5/5] {SHEET_NAMES['DIVIDEND']} → dividends ...")
    ws = spreadsheet.worksheet(SHEET_NAMES["DIVIDEND"])
    results["dividends"] = migrate_dividends(conn, ws)

    conn.close()

    # 結果サマリー
    print("\n========== 移行完了 ==========")
    for table, count in results.items():
        print(f"  {table:<20}: {count:>6} 件")
    total = sum(results.values())
    print(f"  {'合計':<20}: {total:>6} 件")
    print(f"  DB ファイル: {db_path}")


if __name__ == "__main__":
    main()
