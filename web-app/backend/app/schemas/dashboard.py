from pydantic import BaseModel


class KpiSummary(BaseModel):
    totalValue: float       # 評価額合計（円）
    totalProfit: float      # 損益合計（円）
    profitRate: float       # 損益率（%）
    baseDate: str           # 基準日
    portfolioCagr: float | None  # ポートフォリオ全体 CAGR（%）


class AllocationItem(BaseModel):
    name: str               # 銘柄名
    value: float            # 評価額（円）
    percentage: float       # 構成比（%）


class LatestProfitItem(BaseModel):
    name: str               # 銘柄名
    profit: float           # 損益（円）
    profitRate: float       # 損益率（%）


class DashboardResponse(BaseModel):
    kpi: KpiSummary
    allocation: list[AllocationItem]
    latestProfits: list[LatestProfitItem]
