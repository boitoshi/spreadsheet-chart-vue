from collections import defaultdict

from fastapi import APIRouter

from app.schemas.exposure import ExposureItem, ExposureResponse
from app.sheets.performance import fetch_performance

router = APIRouter()

# 対象通貨（HKD は除外）
TARGET_CURRENCIES = {"JPY", "USD"}


@router.get("/exposure", response_model=ExposureResponse)
async def get_exposure() -> ExposureResponse:
    """通貨別エクスポージャーサマリーを返す（最新月、JPY/USD のみ）"""
    records = fetch_performance()
    if not records:
        return ExposureResponse(items=[])

    # 最新月を特定
    latest_date = max(r["date"] for r in records)
    latest_records = [r for r in records if r["date"] == latest_date]

    # 通貨別に集計
    agg: dict[str, dict] = defaultdict(lambda: {"value": 0.0, "cost": 0.0})
    for r in latest_records:
        currency = str(r.get("currency", "JPY"))
        if currency not in TARGET_CURRENCIES:
            continue
        agg[currency]["value"] += r["value"]
        agg[currency]["cost"] += r["cost"]

    total_value = sum(v["value"] for v in agg.values())

    items = []
    for currency in sorted(agg.keys()):
        v = agg[currency]
        profit = v["value"] - v["cost"]
        profit_rate = profit / v["cost"] * 100 if v["cost"] else 0.0
        percentage = v["value"] / total_value * 100 if total_value else 0.0
        items.append(
            ExposureItem(
                currency=currency,
                value=round(v["value"], 0),
                cost=round(v["cost"], 0),
                profit=round(profit, 0),
                profitRate=round(profit_rate, 2),
                percentage=round(percentage, 2),
            )
        )
    return ExposureResponse(items=items)
