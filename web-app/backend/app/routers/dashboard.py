from fastapi import APIRouter

from app.schemas.dashboard import (
    AllocationItem,
    DashboardResponse,
    KpiSummary,
    LatestProfitItem,
)
from app.sheets.performance import fetch_performance
from app.sheets.portfolio import fetch_portfolio
from app.sheets.utils import calc_cagr

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard() -> DashboardResponse:
    """ダッシュボード用データ（KPI・構成比・最新月損益）を返す"""
    records = fetch_performance()
    if not records:
        return DashboardResponse(
            kpi=KpiSummary(
                totalValue=0,
                totalProfit=0,
                profitRate=0,
                baseDate="",
                portfolioCagr=None,
            ),
            allocation=[],
            latestProfits=[],
        )

    # 最新日付を特定
    latest_date = max(r["date"] for r in records)
    latest = [r for r in records if r["date"] == latest_date]

    # KPI 集計
    total_value = sum(r["value"] for r in latest)
    total_profit = sum(r["profit"] for r in latest)
    total_cost = sum(r["cost"] for r in latest)
    profit_rate = (total_profit / total_cost * 100) if total_cost else 0.0

    # ポートフォリオ全体 CAGR（加重平均）
    latest_values = {r["code"]: r["value"] for r in latest}
    portfolio_items = fetch_portfolio()
    cagr_num, cagr_denom = 0.0, 0.0
    for pi in portfolio_items:
        val = latest_values.get(pi["code"], 0.0)
        c = calc_cagr(pi["totalCost"], val, pi["acquiredDate"])
        if c is not None and val > 0:
            cagr_num += c * val
            cagr_denom += val
    portfolio_cagr = round(cagr_num / cagr_denom * 100, 2) if cagr_denom > 0 else None

    # 構成比（DonutChart 用）
    allocation = []
    for r in latest:
        pct = (r["value"] / total_value * 100) if total_value else 0.0
        allocation.append(
            AllocationItem(
                name=r["name"],
                value=r["value"],
                percentage=round(pct, 2),
            )
        )
    allocation.sort(key=lambda x: x.value, reverse=True)

    # 最新月損益（BarChart 用）
    latest_profits = [
        LatestProfitItem(
            name=r["name"],
            profit=r["profit"],
            profitRate=r["profitRate"],
        )
        for r in latest
    ]
    latest_profits.sort(key=lambda x: x.profit, reverse=True)

    return DashboardResponse(
        kpi=KpiSummary(
            totalValue=total_value,
            totalProfit=total_profit,
            profitRate=round(profit_rate, 2),
            baseDate=latest_date,
            portfolioCagr=portfolio_cagr,
        ),
        allocation=allocation,
        latestProfits=latest_profits,
    )
