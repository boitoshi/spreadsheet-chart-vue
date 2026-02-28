from app.sheets.client import get_sheet


def fetch_performance(stock: str | None = None) -> list[dict]:
    """損益レポートシートから月次損益データを取得"""
    sheet = get_sheet("PERFORMANCE")
    records = sheet.get_all_records()
    result = []
    for r in records:
        if not r.get("銘柄コード") or not r.get("日付"):
            continue
        code = str(r["銘柄コード"])
        if stock and code != stock:
            continue
        result.append({
            "date": str(r["日付"]),
            "code": code,
            "name": str(r.get("銘柄名", "")),
            "acquiredPrice": _to_float(r.get("取得単価", 0)),
            "currentPrice": _to_float(r.get("月末価格", 0)),
            "shares": _to_float(r.get("保有株数", 0)),
            "cost": _to_float(r.get("取得額", 0)),
            "value": _to_float(r.get("評価額", 0)),
            "profit": _to_float(r.get("損益", 0)),
            "profitRate": _to_float(r.get("損益率(%)", 0)),
        })
    return result


def _to_float(value) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0
