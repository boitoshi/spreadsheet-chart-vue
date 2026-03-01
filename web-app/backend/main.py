from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import currency, dashboard, dividend, history, portfolio, reports

app = FastAPI(title="ポートフォリオ管理 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(currency.router, prefix="/api")
app.include_router(dividend.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
