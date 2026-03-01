from collections import defaultdict

import yfinance as yf
from fastapi import APIRouter

from app.schemas.benchmark import BenchmarkPoint, BenchmarkResponse
from app.sheets.performance import fetch_performance

router = APIRouter()


@router.get("/benchmark", response_model=BenchmarkResponse)
async def get_benchmark() -> BenchmarkResponse:
    """ポートフォリオとベンチマーク（日経225・S&P500）の累積リターン比較を返す"""
    records = fetch_performance()
    if not records:
        return BenchmarkResponse(data=[])

    # 月ごとに value/cost を集計
    monthly: dict[str, dict] = defaultdict(lambda: {"value": 0.0, "cost": 0.0})
    for r in records:
        monthly[r["date"]]["value"] += r["value"]
        monthly[r["date"]]["cost"] += r["cost"]
    sorted_dates = sorted(monthly.keys())

    # 最初の月から yfinance でベンチマークを取得
    first_date = sorted_dates[0]  # "YYYY-MM-末" 形式
    first_year, first_month = int(first_date[:4]), int(first_date[5:7])
    start_str = f"{first_year}-{first_month:02d}-01"

    try:
        df = yf.download(
            "^N225 ^GSPC",
            start=start_str,
            interval="1mo",
            auto_adjust=True,
            progress=False,
        )["Close"]
        bench: dict[tuple[int, int], dict] = {}
        for ts, row in df.iterrows():
            key = (ts.year, ts.month)
            bench[key] = {
                "nikkei225": float(row.get("^N225", 0) or 0),
                "sp500": float(row.get("^GSPC", 0) or 0),
            }
    except Exception:
        bench = {}

    # 基準値（最初の月）
    base_key = (first_year, first_month)
    base_n225 = bench.get(base_key, {}).get("nikkei225", 0)
    base_sp500 = bench.get(base_key, {}).get("sp500", 0)

    result = []
    for date_str in sorted_dates:
        m = monthly[date_str]
        portfolio_rate = (
            (m["value"] - m["cost"]) / m["cost"] * 100 if m["cost"] else 0.0
        )
        year, month = int(date_str[:4]), int(date_str[5:7])
        bdata = bench.get((year, month), {})
        n225_val = bdata.get("nikkei225", 0)
        sp500_val = bdata.get("sp500", 0)
        n225 = (n225_val / base_n225 - 1) * 100 if base_n225 and n225_val else None
        sp500 = (sp500_val / base_sp500 - 1) * 100 if base_sp500 and sp500_val else None
        result.append(
            BenchmarkPoint(
                date=date_str,
                portfolio=round(portfolio_rate, 2),
                nikkei225=round(n225, 2) if n225 is not None else None,
                sp500=round(sp500, 2) if sp500 is not None else None,
            )
        )
    return BenchmarkResponse(data=result)
