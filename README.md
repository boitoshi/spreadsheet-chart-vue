# 📊 Vue.js Portfolio Tracker

ポケモン世代のための投資ポートフォリオ管理アプリケーション

## 🎯 概要

このアプリケーションは、個人投資家向けのポートフォリオ管理と月次レポート生成を行うWebアプリケーションです。Vue.js（フロントエンド）とDjango（バックエンド）で構築されており、Google Sheetsとの連携による柔軟なデータ管理が特徴です。

## ✨ 主な機能

### 📈 ポートフォリオ管理
- 保有銘柄の管理と損益計算
- リアルタイムでの資産評価額表示
- 詳細な取引履歴の記録

### 📊 ビジュアルレポート
- 資産推移のチャート表示
- 損益分析グラフ
- セクター別構成の可視化

### 📝 月次レポート生成
- 自動的な月次投資成績レポート作成
- 複数形式での出力（HTML、Markdown、PDF）
- ブログ投稿用コンテンツの生成

### 🔧 手動データ管理
- 株価データの手動入力・更新
- CSVファイルからの一括インポート
- 取引履歴の編集・削除

### 📤 エクスポート機能
- 画像形式でのチャート出力
- WordPress用JSON形式での出力
- SNSシェア機能

## 🏗️ 技術スタック

### フロントエンド
- **Vue.js 3** - メインフレームワーク
- **Vue Router** - ルーティング管理
- **Chart.js** - データ可視化
- **Axios** - HTTP通信
- **Vite** - ビルドツール

### バックエンド
- **Django** - Webフレームワーク
- **Google Sheets API** - データストレージ
- **Python pandas** - データ処理

### その他
- **html2canvas** - 画像エクスポート
- **marked** - Markdown処理
- **file-saver** - ファイル保存

## 📁 プロジェクト構成

```
spreadsheet-chart-vue/
├── frontend/                    # Vue.js フロントエンド
│   ├── src/
│   │   ├── components/         # Vueコンポーネント
│   │   │   ├── BlogExport.vue
│   │   │   ├── LineChart.vue
│   │   │   ├── PortfolioDashboard.vue
│   │   │   ├── ProfitChart.vue
│   │   │   ├── Spreadsheet.vue
│   │   │   └── StockTable.vue
│   │   ├── views/              # ページコンポーネント
│   │   │   ├── Dashboard.vue
│   │   │   ├── ManualInput.vue
│   │   │   └── MonthlyReport.vue
│   │   ├── composables/        # Vue Composition API
│   │   │   ├── useChartExport.js
│   │   │   ├── usePortfolioData.js
│   │   │   └── useSpreadsheetData.js
│   │   ├── router/             # ルーティング設定
│   │   └── utils/              # ユーティリティ関数
│   └── package.json
├── backend/                     # Django バックエンド
│   ├── sheets_api/             # メインアプリケーション
│   │   ├── views.py           # データ取得API
│   │   ├── manual_updater.py  # 手動更新API
│   │   ├── report_generator.py # レポート生成API
│   │   └── urls.py
│   ├── templates/              # HTMLテンプレート
│   │   └── report_template.html
│   └── requirements.txt
├── docs/                        # ドキュメント
│   └── monthly-reports/        # 月次レポートアーカイブ
│       ├── README.md
│       └── templates/
└── README.md
```

## 🚀 セットアップ

### 前提条件
- Node.js 16+
- Python 3.8+
- Google Sheets API の認証情報

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

### バックエンド

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 環境変数設定

```bash
# backend/.env
GOOGLE_SHEETS_ID=your_spreadsheet_id
GOOGLE_SHEETS_CREDENTIALS=path_to_service_account.json
```

## 📖 使用方法

### 1. ダッシュボード
- `http://localhost:3000/` でアクセス
- ポートフォリオ全体の概要を確認

### 2. 手動データ入力
- `/input` で株価データの手動入力
- CSVファイルからの一括インポート

### 3. 月次レポート
- `/report/2024-01` で指定月のレポート表示
- 複数形式でのエクスポート

## 🔧 API エンドポイント

### データ取得
- `GET /api/get_data/` - スプレッドシートデータ取得

### 手動更新
- `POST /api/update_stock_price/` - 株価更新
- `POST /api/bulk_update_prices/` - 一括価格更新
- `POST /api/save_monthly_data/` - 月次データ保存

### レポート生成
- `GET /api/generate_report/{month}/` - 月次レポート生成
- `GET /api/generate_blog_content/{month}/` - ブログ用コンテンツ生成

## 📊 データ形式

### ポートフォリオデータ
```json
{
  "ticker": "7974",
  "name": "任天堂",
  "quantity": 100,
  "avg_price": 5600,
  "current_price": 6500,
  "market_value": 650000,
  "profit": 90000,
  "profit_rate": 16.1
}
```

### 月次レポートデータ
```json
{
  "month": "2024-01",
  "summary": {
    "total_value": 1456789,
    "total_profit": 234567,
    "monthly_profit": 45320
  },
  "portfolio": [...],
  "commentary": "今月の所感..."
}
```

## 🎨 カスタマイズ

### テーマカラー
`frontend/src/style.css` でカラーパレットを変更可能

### レポートテンプレート
`backend/templates/report_template.html` でHTMLレポートの外観をカスタマイズ

### ブログテンプレート
`docs/monthly-reports/templates/blog-template.md` でブログ投稿用テンプレートを編集

## 🔒 セキュリティ

- Google Sheets API認証情報は環境変数で管理
- センシティブなデータは `.gitignore` で除外
- 個人の投資情報保護のため、公開リポジトリでの管理は非推奨

## 📝 ライセンス

このプロジェクトは個人用途での使用を想定しています。

## 🤝 コントリビューション

プルリクエストや Issue の投稿を歓迎します。

## 📞 サポート

質問や不具合報告は GitHub Issues でお願いします。

---

**重要**: このツールは個人的な投資記録を目的としており、投資アドバイスを提供するものではありません。投資は自己責任で行ってください。