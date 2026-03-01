from pydantic import BaseModel


class ReportItem(BaseModel):
    year: int
    month: int
    label: str
    filename: str


class ReportListResponse(BaseModel):
    reports: list[ReportItem]


class ReportContentResponse(BaseModel):
    year: int
    month: int
    content: str
