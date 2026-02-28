from pydantic import BaseModel


class CurrencyRatePoint(BaseModel):
    date: str
    pair: str
    rate: float
    changeRate: float | None
    high: float | None
    low: float | None


class CurrencyResponse(BaseModel):
    data: list[CurrencyRatePoint]
    latestRate: float
