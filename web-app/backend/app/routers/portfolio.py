from fastapi import APIRouter

from app.schemas.portfolio import PortfolioItem, PortfolioResponse
from app.sheets.performance import fetch_latest_values
from app.sheets.portfolio import fetch_portfolio
from app.sheets.utils import calc_cagr

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio() -> PortfolioResponse:
    """保有銘柄一覧を返す"""
    portfolio = fetch_portfolio()
    latest_values = fetch_latest_values()
    items = []
    for item in portfolio:
        current_value = latest_values.get(item["code"], 0.0)
        cagr = calc_cagr(item["totalCost"], current_value, item["acquiredDate"])
        items.append(PortfolioItem(**item, currentValue=current_value, cagr=cagr))
    return PortfolioResponse(items=items)
