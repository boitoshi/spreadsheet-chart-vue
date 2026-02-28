from app.sheets.client import get_sheet


def fetch_portfolio() -> list[dict]:
    """ポートフォリオシートから全保有銘柄を取得"""
    sheet = get_sheet("PORTFOLIO")
    records = sheet.get_all_records()
    result = []
    for r in records:
        # 空行スキップ
        if not r.get("銘柄コード"):
            continue
        result.append({
            "code": r["銘柄コード"],
            "name": r["銘柄名"],
            "acquiredDate": str(r.get("取得日", "")),
            "acquiredPriceJpy": _to_float(r.get("取得単価（円）", 0)),
            "acquiredPriceForeign": _to_float_or_none(r.get("取得単価（外貨）")),
            "acquiredExchangeRate": _to_float_or_none(r.get("取得時為替レート")),
            "shares": _to_float(r.get("保有株数", 0)),
            "totalCost": _to_float(r.get("取得額合計", 0)),
            "currency": str(r.get("通貨", "JPY")),
            "isForeign": r.get("外国株フラグ", "×") == "○",
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
