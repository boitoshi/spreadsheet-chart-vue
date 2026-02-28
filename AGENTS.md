# Repository Guidelines

## Project Overview

Next.js + FastAPI による個人投資ポートフォリオ管理アプリケーション。
Google Sheets をデータストアとして使用し、資産管理・月次レポート生成・チャート表示を行う。

## Project Structure

```
spreadsheet-chart-vue/
├── data-collector/         # 月次データ収集（yfinance → Google Sheets）
│   ├── collectors/         # 株価収集・Sheets書き込み・チャート生成
│   ├── config/             # 銘柄リスト等の設定
│   ├── schedulers/         # 月次スケジューラー
│   ├── output/             # ブログ下書き・チャート画像
│   └── main.py             # エントリーポイント
├── shared/
│   └── sheets_config.py    # シートヘッダー定義（一元管理）
├── web-app/
│   ├── backend/            # FastAPI + gspread
│   │   ├── main.py         # エントリー・CORS・ルーター
│   │   ├── .env            # SPREADSHEET_ID, GOOGLE_APPLICATION_CREDENTIALS
│   │   └── app/
│   │       ├── config.py       # pydantic-settings
│   │       ├── sheets/         # Google Sheets 読み取りモジュール
│   │       ├── routers/        # FastAPI ルーター
│   │       └── schemas/        # Pydantic スキーマ
│   └── frontend/           # Next.js 16 + Tailwind v4 + Recharts
│       └── src/
│           ├── app/            # App Router ページ
│           ├── components/     # UI コンポーネント（Server/Client分離）
│           ├── lib/            # api.ts, formatters.ts
│           └── types/          # TypeScript 型定義
└── docs/                   # ドキュメント
```

## Build & Dev Commands

### Backend (FastAPI on port 8000)
```bash
cd web-app/backend
uv sync
uv run uvicorn main:app --reload
```

### Frontend (Next.js on port 3000)
```bash
cd web-app/frontend
npm install
npm run dev       # 開発サーバー
npm run build     # 本番ビルド（型チェック含む）
```

### Data Collector (monthly batch)
```bash
cd data-collector
uv sync --dev
uv run python main.py               # 対話型
uv run python main.py 2024 12       # バッチ実行
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | ヘルスチェック |
| GET | `/api/dashboard` | KPI・構成比・最新月損益 |
| GET | `/api/portfolio` | 保有銘柄一覧 |
| GET | `/api/history` | 月次損益推移（`?stock=コード`）|
| GET | `/api/currency` | 為替レート推移（`?start=YYYY-MM`）|

## Coding Style

- **Python**: ruff (select = E, F, I), Python 3.12, type hints 必須, コメント日本語
- **TypeScript/Next.js**: strict mode, Server Components でデータフェッチ, Recharts コンポーネントは `"use client"`
- **Env**: secrets は `.env` で管理、VCS にコミットしない
- **コミット**: 日本語・簡潔に（例: `API: dashboard エンドポイント実装`）

## Quality Checks

```bash
# Python
cd web-app/backend && uv run ruff check . --fix
cd data-collector && uv run ruff check . --fix

# TypeScript/Next.js
cd web-app/frontend && npm run build   # 型エラーを検出
```

## Environment Variables

- `web-app/backend/.env`: `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`
- `data-collector/.env`: `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`
- `web-app/frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL`
