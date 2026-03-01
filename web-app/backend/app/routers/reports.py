from fastapi import APIRouter, HTTPException, Path

from app.reports import list_reports, read_report
from app.schemas.reports import (
    ReportContentResponse,
    ReportItem,
    ReportListResponse,
)

router = APIRouter()


@router.get("/reports", response_model=ReportListResponse)
async def get_reports() -> ReportListResponse:
    """利用可能なレポート一覧を返す"""
    items = list_reports()
    return ReportListResponse(reports=[ReportItem(**r) for r in items])


@router.get("/reports/{year}/{month}", response_model=ReportContentResponse)
async def get_report(
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
) -> ReportContentResponse:
    """指定年月のレポート内容を返す"""
    content = read_report(year, month)
    if content is None:
        raise HTTPException(status_code=404, detail="レポートが見つかりません")
    return ReportContentResponse(year=year, month=month, content=content)
