from app.sheets.client import get_sheet
from app.sheets.utils import to_float, to_float_or_none


def fetch_currency(start: str | None = None) -> list[dict]:
    """為替レートシートからデータを取得（start=YYYY-MM でフィルタ可能）"""
    sheet = get_sheet("CURRENCY")
    records = sheet.get_all_records()
    result = []
    for r in records:
        if not r.get("取得日") or not r.get("通貨ペア"):
            continue
        date_str = str(r["取得日"])
        # start より前の日付をスキップ（"YYYY-MM-DD" と "YYYY-MM" は辞書順比較可能）
        if start and date_str < start:
            continue
        result.append({
            "date": date_str,
            "pair": str(r["通貨ペア"]),
            "rate": to_float(r.get("レート", 0)),
            "changeRate": to_float_or_none(r.get("変動率(%)")),
            "high": to_float_or_none(r.get("最高値")),
            "low": to_float_or_none(r.get("最安値")),
        })
    return result
