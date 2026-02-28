from fastapi import APIRouter, Query

from app.schemas.currency import CurrencyRatePoint, CurrencyResponse
from app.sheets.currency import fetch_currency

router = APIRouter()


@router.get("/currency", response_model=CurrencyResponse)
async def get_currency(
    start: str | None = Query(default=None, description="開始年月（YYYY-MM）"),
) -> CurrencyResponse:
    """為替レート推移を返す"""
    records = fetch_currency(start=start)
    data = [CurrencyRatePoint(**r) for r in records]
    latest_rate = data[-1].rate if data else 0.0
    return CurrencyResponse(data=data, latestRate=latest_rate)
