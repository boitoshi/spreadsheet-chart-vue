from fastapi import APIRouter

from app.schemas.dividend import DividendItem, DividendResponse
from app.sheets.dividend import fetch_dividend

router = APIRouter()


@router.get("/dividend", response_model=DividendResponse)
async def get_dividend() -> DividendResponse:
    """配当・分配金一覧を返す"""
    records = fetch_dividend()
    data = [DividendItem(**r) for r in records]
    total_jpy = sum(item.totalJpy for item in data)
    return DividendResponse(data=data, totalJpy=total_jpy)
