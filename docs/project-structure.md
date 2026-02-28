# プロジェクト構成

## ディレクトリ構成

```
spreadsheet-chart-vue/
├── data-collector/         # データ収集フロー（独立実行）
│   ├── collectors/         # 株価収集・Sheets書き込み・チャート生成
│   ├── config/             # 設定ファイル（銘柄リスト等）
│   ├── schedulers/         # 月次実行スケジューラー
│   ├── output/             # 生成ファイル（ブログ下書き・チャート画像）
│   ├── logs/               # 実行ログ
│   ├── pyproject.toml
│   └── main.py             # メイン実行スクリプト
├── web-app/
│   ├── backend/            # FastAPI REST API
│   │   ├── main.py         # エントリー・CORS・ルーター登録
│   │   ├── pyproject.toml
│   │   ├── .env            # SPREADSHEET_ID, GOOGLE_APPLICATION_CREDENTIALS
│   │   └── app/
│   │       ├── config.py          # pydantic-settings 環境変数管理
│   │       ├── sheets/            # Google Sheets 読み取りモジュール
│   │       │   ├── client.py      # gspread 認証シングルトン
│   │       │   ├── portfolio.py   # ポートフォリオシート
│   │       │   ├── performance.py # 損益レポートシート
│   │       │   └── currency.py    # 為替レートシート
│   │       ├── routers/           # FastAPI ルーター
│   │       │   ├── dashboard.py
│   │       │   ├── portfolio.py
│   │       │   ├── history.py
│   │       │   └── currency.py
│   │       └── schemas/           # Pydantic スキーマ
│   │           ├── dashboard.py
│   │           ├── portfolio.py
│   │           ├── history.py
│   │           └── currency.py
│   └── frontend/           # Next.js 16 アプリケーション
│       ├── next.config.ts  # API リライト（/api/* → localhost:8000）
│       └── src/
│           ├── app/
│           │   ├── layout.tsx      # ナビゲーション共通レイアウト
│           │   ├── page.tsx        # / ダッシュボード
│           │   ├── portfolio/page.tsx
│           │   ├── history/page.tsx
│           │   └── currency/page.tsx
│           ├── components/
│           │   ├── dashboard/      # KpiCards, AllocationChart, LatestBarChart
│           │   ├── history/        # ProfitAreaChart, StockFilter
│           │   ├── portfolio/      # HoldingsTable
│           │   └── currency/       # CurrencyLineChart
│           ├── lib/
│           │   ├── api.ts          # fetch ラッパー
│           │   └── formatters.ts   # 通貨・パーセント表示
│           └── types/              # TypeScript 型定義
├── shared/
│   └── sheets_config.py    # スプレッドシートのヘッダー定義（一元管理）
├── docs/                   # ドキュメント
└── PROJECT_PROCEED.md      # 実装状況・課題管理
```

## データフロー

### データ収集フロー（月次バッチ）

```
yfinance API
    ↓
data-collector/main.py
    ↓ 株価データ取得・損益計算・為替換算
collectors/sheets_writer.py
    ↓ Google Sheets API
ポートフォリオシート / データ記録シート / 損益レポートシート / 為替レートシート
    ↓ （副産物）
output/blog_draft_YYYY_MM.md  # ブログ記事下書き
output/YYYY_MM_charts/        # チャート画像・HTML
```

### Webアプリフロー（リアルタイム）

```
Google Sheets
    ↓ gspread
FastAPI API（web-app/backend/app/）
    ↓ JSON
Next.js（web-app/frontend/src/app/）
    ↓ Recharts
ブラウザ（ポートフォリオダッシュボード）
```

## 保有期間フィルタリングの仕様

- ポートフォリオシートの「取得日」（C列）を参照
- **取得月以降**のみ損益レポートに記録
- 取得前の期間はデータ記録（市場データ）のみ記録、損益計算は行わない
- 取得日が空の場合はデフォルトで保有扱い（後方互換性）
