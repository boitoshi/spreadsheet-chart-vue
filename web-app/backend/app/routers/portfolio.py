from fastapi import APIRouter

from app.schemas.portfolio import PortfolioItem, PortfolioResponse
from app.sheets.portfolio import fetch_portfolio

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio() -> PortfolioResponse:
    """保有銘柄一覧を返す"""
    items = fetch_portfolio()
    return PortfolioResponse(items=[PortfolioItem(**item) for item in items])
