from pydantic import BaseModel


class PortfolioItem(BaseModel):
    code: str
    name: str
    acquiredDate: str
    acquiredPriceJpy: float
    acquiredPriceForeign: float | None
    acquiredExchangeRate: float | None
    shares: float
    totalCost: float
    currency: str
    isForeign: bool
    currentValue: float
    cagr: float | None


class PortfolioResponse(BaseModel):
    items: list[PortfolioItem]
