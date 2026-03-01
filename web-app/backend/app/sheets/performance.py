from app.sheets.client import get_sheet
from app.sheets.utils import to_float, to_float_or_none


def calc_profit(
    profit: float,
    shares: float,
    currency: str,
    acquired_price_foreign: float | None,
    current_price_foreign: float | None,
    acquired_exchange_rate: float | None,
    current_exchange_rate: float | None,
) -> tuple[float, float]:
    """損益分離計算。(株価損益, 為替損益) を返す"""
    if (
        currency == "JPY"
        or acquired_price_foreign is None
        or current_price_foreign is None
        or acquired_exchange_rate is None
        or current_exchange_rate is None
    ):
        return profit, 0.0
    price_diff = current_price_foreign - acquired_price_foreign
    stock_profit = price_diff * acquired_exchange_rate * shares
    rate_diff = current_exchange_rate - acquired_exchange_rate
    fx_profit = rate_diff * current_price_foreign * shares
    return stock_profit, fx_profit


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

        stock_profit, fx_profit = calc_profit(
            profit,
            shares,
            currency,
            acquired_price_foreign,
            current_price_foreign,
            acquired_exchange_rate,
            current_exchange_rate,
        )

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


def fetch_latest_values() -> dict[str, float]:
    """銘柄コード → 最新月末評価額 の辞書を返す"""
    records = fetch_performance()
    if not records:
        return {}
    latest_date = max(r["date"] for r in records)
    return {r["code"]: r["value"] for r in records if r["date"] == latest_date}
