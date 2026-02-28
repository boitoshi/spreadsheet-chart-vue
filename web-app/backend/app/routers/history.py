from fastapi import APIRouter, Query

from app.schemas.history import HistoryResponse, MonthlyProfitPoint
from app.sheets.performance import fetch_performance

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    stock: str | None = Query(default=None, description="銘柄コードでフィルター"),
) -> HistoryResponse:
    """月次損益推移を返す"""
    # 全件を1回だけ取得してメモリ内でフィルター（Sheets API 呼び出しを節約）
    all_records = fetch_performance()
    symbols = sorted({r["code"] for r in all_records})
    filtered = [r for r in all_records if not stock or r["code"] == stock]
    data = [MonthlyProfitPoint(**r) for r in filtered]
    return HistoryResponse(data=data, symbols=symbols)
