# Portfolio Tracker

個人投資ポートフォリオ管理アプリケーション。Google Sheets をデータストアとして、資産管理・月次レポート生成・チャート表示を行う。

## 技術スタック

| 役割 | 技術 |
|------|------|
| フロントエンド | Next.js 16, Tailwind CSS v4, Recharts, TypeScript |
| バックエンド | FastAPI, gspread, uvicorn（uv 管理）|
| データ収集 | Python（yfinance → Google Sheets）|
| データストア | Google Sheets |

## ディレクトリ構成

```
spreadsheet-chart-vue/
├── data-collector/         # 月次データ収集バッチ
├── shared/
│   └── sheets_config.py   # シートヘッダー定義（一元管理）
├── web-app/
│   ├── backend/            # FastAPI REST API（ポート8000）
│   └── frontend/           # Next.js アプリ（ポート3000）
└── docs/                   # ドキュメント
```

## セットアップ

### 前提条件

- Python 3.12 以上
- uv（Astral）
- Node.js 22 以上
- Google Sheets API サービスアカウント認証情報

### 1. バックエンド

```bash
cd web-app/backend
uv sync

# .env を作成
cat > .env << 'EOF'
SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
EOF
```

### 2. フロントエンド

```bash
cd web-app/frontend
npm install
```

### 3. データ収集

```bash
cd data-collector
uv sync --dev

# .env を作成
cat > .env << 'EOF'
SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
EOF
```

## 起動方法

```bash
# バックエンド（ポート8000）
cd web-app/backend && uv run uvicorn main:app --reload

# フロントエンド（ポート3000）
cd web-app/frontend && npm run dev

# データ収集（月次バッチ）
cd data-collector && uv run python main.py
```

## API エンドポイント

| パス | 説明 |
|------|------|
| GET `/health` | ヘルスチェック |
| GET `/api/dashboard` | KPI・構成比・最新月損益 |
| GET `/api/portfolio` | 保有銘柄一覧 |
| GET `/api/history` | 月次損益推移（`?stock=コード`）|
| GET `/api/currency` | 為替レート推移（`?start=YYYY-MM`）|

詳細は [`docs/api-reference.md`](docs/api-reference.md) を参照。

## 品質チェック

```bash
# Python lint
cd web-app/backend && uv run ruff check . --fix
cd data-collector && uv run ruff check . --fix

# TypeScript / ビルド確認
cd web-app/frontend && npm run build
```

## ドキュメント

- [`docs/project-structure.md`](docs/project-structure.md) — ディレクトリ構成・データフロー
- [`docs/sheets-schema.md`](docs/sheets-schema.md) — スプレッドシートのカラム定義
- [`docs/api-reference.md`](docs/api-reference.md) — API エンドポイント詳細
- [`docs/deployment-plan.md`](docs/deployment-plan.md) — デプロイ方針（Cloud Run + CONOHA）
- [`docs/data-collection-guide.md`](docs/data-collection-guide.md) — データ収集の操作ガイド
- [`data-collector/README.md`](data-collector/README.md) — データ収集システム詳細

## 注意事項

- このツールは個人的な投資記録を目的としており、投資アドバイスを提供するものではありません
- サービスアカウント JSON は `.gitignore` で除外し、VCS にコミットしないこと
- 個人の投資情報が含まれるため、公開リポジトリでの管理は非推奨
