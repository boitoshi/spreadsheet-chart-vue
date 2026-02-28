import os
import sys
from functools import lru_cache

import gspread
from google.oauth2.service_account import Credentials

# shared/sheets_config.py をインポートするためのパス設定
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "shared"),
)
from sheets_config import SCOPES, SHEET_NAMES  # noqa: E402

from app.config import get_settings  # noqa: E402


@lru_cache(maxsize=1)
def get_spreadsheet() -> gspread.Spreadsheet:
    """gspread スプレッドシートシングルトンを返す"""
    settings = get_settings()
    creds = Credentials.from_service_account_file(
        settings.google_application_credentials, scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(settings.spreadsheet_id)


def get_sheet(sheet_key: str) -> gspread.Worksheet:
    """SHEET_NAMES のキーでワークシートを取得する"""
    spreadsheet = get_spreadsheet()
    return spreadsheet.worksheet(SHEET_NAMES[sheet_key])
