from pydantic import BaseModel


class MonthlyProfitPoint(BaseModel):
    date: str
    code: str
    name: str
    profit: float
    value: float
    profitRate: float
    currency: str
    stockProfit: float
    fxProfit: float


class HistoryResponse(BaseModel):
    data: list[MonthlyProfitPoint]
    symbols: list[str]
