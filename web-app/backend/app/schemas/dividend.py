from pydantic import BaseModel


class DividendItem(BaseModel):
    date: str
    code: str
    name: str
    dividendForeign: float
    shares: float
    totalForeign: float
    currency: str
    exchangeRate: float
    totalJpy: float


class DividendResponse(BaseModel):
    data: list[DividendItem]
    totalJpy: float
