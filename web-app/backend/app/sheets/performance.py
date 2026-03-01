from app.sheets.client import get_sheet
from app.sheets.utils import to_float, to_float_or_none


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
        profit = to_float(r.get("損益", 0))
        shares = to_float(r.get("保有株数", 0))
        currency = str(r.get("通貨", "JPY"))

        acquired_price_foreign = to_float_or_none(r.get("取得単価（外貨）"))
        current_price_foreign = to_float_or_none(r.get("月末価格（外貨）"))
        acquired_exchange_rate = to_float_or_none(r.get("取得時為替レート"))
        current_exchange_rate = to_float_or_none(r.get("現在為替レート"))

        if (
            currency == "JPY"
            or acquired_price_foreign is None
            or current_price_foreign is None
            or acquired_exchange_rate is None
            or current_exchange_rate is None
        ):
            stock_profit = profit
            fx_profit = 0.0
        else:
            price_diff = current_price_foreign - acquired_price_foreign
            stock_profit = price_diff * acquired_exchange_rate * shares
            rate_diff = current_exchange_rate - acquired_exchange_rate
            fx_profit = rate_diff * current_price_foreign * shares

        result.append({
            "date": str(r["日付"]),
            "code": code,
            "name": str(r.get("銘柄名", "")),
            "cost": to_float(r.get("取得額", 0)),
            "value": to_float(r.get("評価額", 0)),
            "profit": profit,
            "profitRate": to_float(r.get("損益率(%)", 0)),
            "currency": currency,
            "stockProfit": stock_profit,
            "fxProfit": fx_profit,
        })
    return result
