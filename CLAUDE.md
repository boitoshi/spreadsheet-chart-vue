# Claude Code プロジェクト設定

## プロジェクト概要
Vue.js + Django による投資ポートフォリオ管理アプリケーション。Google Sheetsと連携し、資産管理・月次レポート生成・チャート表示を行う。

## 技術スタック
- **フロントエンド**: Vue.js 3, Vue Router, Chart.js, Vite
- **バックエンド**: Django, Google Sheets API, Python pandas
- **言語**: JavaScript/Vue.js (フロント), Python (バック)

## ディレクトリ構成
```
spreadsheet-chart-vue/
├── frontend/           # Vue.js アプリケーション
│   ├── src/
│   │   ├── components/ # Vue コンポーネント
│   │   ├── views/      # ページコンポーネント  
│   │   ├── composables/# Composition API
│   │   ├── router/     # ルーティング
│   │   └── utils/      # ユーティリティ
│   └── package.json
├── backend/            # Django API
│   ├── sheets/         # メインアプリ
│   ├── portfolio/      # ポートフォリオ管理
│   └── requirements.txt
└── docs/               # ドキュメント
```

## 開発コマンド

### フロントエンド
- **開発サーバー**: `cd frontend && npm run dev`
- **ビルド**: `cd frontend && npm run build`
- **プレビュー**: `cd frontend && npm run preview`

### バックエンド  
- **開発サーバー**: `cd backend && python manage.py runserver`
- **マイグレーション**: `cd backend && python manage.py migrate`
- **依存関係インストール**: `cd backend && pip install -r requirements.txt`

### 株価データ取得スクリプト
- **月次株価取得**: `cd script && python stock_app.py`
- **環境変数設定**: backend/.env ファイルで GOOGLE_APPLICATION_CREDENTIALS と SPREADSHEET_ID を設定
- **機能**: ポートフォリオ管理・月次株価データ取得・損益レポート生成
- **シート構成**: ポートフォリオ（銘柄管理）、データ記録（Django backend用）、損益レポート

## 主要コンポーネント
- `ProfitChart.vue` - 損益推移チャート
- `PortfolioDashboard.vue` - ポートフォリオダッシュボード
- `BlogExport.vue` - ブログエクスポート機能
- `MonthlyReport.vue` - 月次レポート表示

## データフロー
1. **株価データ取得**: script/stock_app.py → yfinance API → Google Sheets転記（月1回実行）
2. **データ読み取り**: Google Sheets → Django API → Vue.js フロントエンド
3. **チャート表示**: Chart.js による損益推移・ポートフォリオ可視化

## API エンドポイント
- `GET /api/get_data/` - スプレッドシートデータ取得
- `POST /api/update_stock_price/` - 株価更新
- `GET /api/generate_report/{month}/` - 月次レポート生成

## 注意事項
- Google Sheets API認証情報が必要
- 個人投資データを扱うため、セキュリティに注意
- 日本語でのコミュニケーション対応

## Claude Code使用時の設定
- 質問・回答は日本語で対応
- コードコメントは日本語で記述
- エラーメッセージも日本語で説明
- Vue.js/Django のベストプラクティス遵守

## 開発ガイドライン
- コンポーネントは単一責任の原則
- Composition API を活用
- レスポンシブデザイン対応
- エラーハンドリングの実装
- テストコード作成推奨