import logging

import gspread

from app.sheets.client import get_sheet
from app.sheets.utils import to_float


def fetch_dividend() -> list[dict]:
    """配当・分配金シートから全データを取得。シートが存在しない場合は空リストを返す"""
    try:
        sheet = get_sheet("DIVIDEND")
        records = sheet.get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        return []
    except Exception:
        logging.exception("配当シート('DIVIDEND')の取得に失敗しました")
        raise
    result = []
    for r in records:
        if not r.get("銘柄コード") or not r.get("受取日"):
            continue
        result.append({
            "date": str(r["受取日"]),
            "code": str(r["銘柄コード"]),
            "name": str(r.get("銘柄名", "")),
            "dividendForeign": to_float(r.get("1株配当（外貨）", 0)),
            "shares": to_float(r.get("保有株数", 0)),
            "totalForeign": to_float(r.get("配当合計（外貨）", 0)),
            "currency": str(r.get("通貨", "JPY")),
            "exchangeRate": to_float(r.get("為替レート", 1)),
            "totalJpy": to_float(r.get("配当合計（円）", 0)),
        })
    return result
