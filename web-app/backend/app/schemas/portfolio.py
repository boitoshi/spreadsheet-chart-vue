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


class PortfolioResponse(BaseModel):
    items: list[PortfolioItem]
