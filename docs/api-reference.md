# API リファレンス

FastAPI バックエンド（ポート8000）のエンドポイント一覧。

## エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/health` | ヘルスチェック |
| GET | `/api/dashboard` | KPI・構成比・最新月損益 |
| GET | `/api/portfolio` | 保有銘柄一覧 |
| GET | `/api/history` | 月次損益推移（`?stock=コード` でフィルター）|
| GET | `/api/currency` | 為替レート推移（`?start=YYYY-MM` で開始月指定）|
| GET | `/api/dividend` | 配当・分配金一覧 |
| GET | `/api/reports` | 月次レポート一覧 |
| GET | `/api/reports/{year}/{month}` | 指定月のレポート内容（Markdown テキスト）|

## レスポンス型

### GET /health

```json
{"status": "ok"}
```

### GET /api/dashboard

```json
{
  "kpi": {
    "totalValue": 5000000.0,
    "totalProfit": 300000.0,
    "profitRate": 6.38,
    "baseDate": "2025-01-末"
  },
  "allocation": [
    {"name": "任天堂", "value": 3000000.0, "percentage": 60.0}
  ],
  "latestProfits": [
    {"name": "任天堂", "profit": 200000.0, "profitRate": 7.14}
  ]
}
```

### GET /api/portfolio

```json
{
  "items": [
    {
      "code": "7974.T",
      "name": "任天堂",
      "acquiredDate": "2023-06-28",
      "acquiredPriceJpy": 6433.0,
      "acquiredPriceForeign": null,
      "acquiredExchangeRate": null,
      "shares": 100.0,
      "totalCost": 643300.0,
      "currency": "JPY",
      "isForeign": false
    }
  ]
}
```

### GET /api/history[?stock=コード]

```json
{
  "data": [
    {
      "date": "2024-01-末",
      "code": "7974.T",
      "name": "任天堂",
      "profit": 50000.0,
      "value": 700000.0,
      "profitRate": 7.5,
      "currency": "JPY",
      "stockProfit": 50000.0,
      "fxProfit": 0.0
    }
  ],
  "symbols": ["2432.T", "7974.T", "NVDA"]
}
```

### GET /api/currency[?start=YYYY-MM]

```json
{
  "data": [
    {
      "date": "2024-01-31",
      "pair": "USD/JPY",
      "rate": 148.12,
      "changeRate": -0.5,
      "high": 149.0,
      "low": 147.5
    }
  ],
  "latestRate": 150.0
}
```

### GET /api/dividend

```json
{
  "data": [
    {
      "date": "2024-12-31",
      "code": "NVDA",
      "name": "エヌビディア",
      "dividendForeign": 0.01,
      "shares": 10.0,
      "totalForeign": 0.1,
      "currency": "USD",
      "exchangeRate": 150.0,
      "totalJpy": 15.0
    }
  ],
  "totalJpy": 15.0
}
```

### GET /api/reports

```json
{
  "reports": [
    {
      "year": 2026,
      "month": 1,
      "label": "2026年1月",
      "filename": "blog_draft_2026_01.md"
    }
  ]
}
```

### GET /api/reports/{year}/{month}

```json
{
  "year": 2026,
  "month": 1,
  "content": "## 2026年1月の投資成績 ..."
}
```

## 実装ファイル対応表

| エンドポイント | ルーター | シートモジュール | スキーマ |
|--------------|---------|----------------|---------|
| /api/dashboard | app/routers/dashboard.py | app/sheets/performance.py | app/schemas/dashboard.py |
| /api/portfolio | app/routers/portfolio.py | app/sheets/portfolio.py | app/schemas/portfolio.py |
| /api/history | app/routers/history.py | app/sheets/performance.py | app/schemas/history.py |
| /api/currency | app/routers/currency.py | app/sheets/currency.py | app/schemas/currency.py |
| /api/dividend | app/routers/dividend.py | app/sheets/dividend.py | app/schemas/dividend.py |
| /api/reports | app/routers/reports.py | app/reports.py | app/schemas/reports.py |
