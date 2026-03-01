from pydantic import BaseModel


class ExposureItem(BaseModel):
    currency: str
    value: float
    cost: float
    profit: float
    profitRate: float
    percentage: float


class ExposureResponse(BaseModel):
    items: list[ExposureItem]
