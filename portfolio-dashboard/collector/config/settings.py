"""設定ファイル（SQLite 版）"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv(Path(__file__).parent.parent / ".env")

GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(
        Path(__file__).parent.parent.parent
        / "data-collector"
        / "config"
        / "my-service-account.json"
    ),
)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
DB_PATH = os.getenv(
    "DB_PATH",
    str(Path(__file__).parent.parent.parent / "data" / "portfolio.db"),
)

# WordPress 設定（ブログ自動投稿用）
WP_URL = os.getenv("WP_URL", "")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

# AI コメント生成（ANTHROPIC_API_KEY は anthropic ライブラリが自動読み取り）
AI_COMMENTS_ENABLED = os.getenv("AI_COMMENTS_ENABLED", "false").lower() == "true"
WP_PUBLISH_ENABLED = os.getenv("WP_PUBLISH_ENABLED", "false").lower() == "true"

# 対応通貨設定
CURRENCY_SETTINGS = {
    "supported_currencies": ["USD", "HKD", "EUR", "GBP"],
    "base_currency": "JPY",
    "foreign_stock_patterns": [".HK", ".L", ".PA", ".DE"],
}
