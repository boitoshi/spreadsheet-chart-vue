from pydantic import BaseModel


class BenchmarkPoint(BaseModel):
    date: str
    portfolio: float
    nikkei225: float | None
    sp500: float | None


class BenchmarkResponse(BaseModel):
    data: list[BenchmarkPoint]
