from app.sheets.client import get_sheet


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
            "rate": _to_float(r.get("レート", 0)),
            "changeRate": _to_float_or_none(r.get("変動率(%)")),
            "high": _to_float_or_none(r.get("最高値")),
            "low": _to_float_or_none(r.get("最安値")),
        })
    return result


def _to_float(value) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _to_float_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None
