# Claude Code プロジェクト設定

## プロジェクト概要
Vue.js + Django による投資ポートフォリオ管理アプリケーション。Google Sheetsと連携し、資産管理・月次レポート生成・チャート表示を行う。

## 技術スタック
- **フロントエンド**: Vue.js 3, Vue Router, Chart.js, Vite
- **バックエンド**: Django, Google Sheets API, Python pandas,uv（パッケージ管理）
- **言語**: TypeScript/Vue.js (フロント), Python (バック)

## ディレクトリ構成
```
spreadsheet-chart-vue/
├── data-collector/     # ①データ収集フロー（独立実行）
│   ├── collectors/     # 株価データ収集・Sheets書き込み
│   ├── config/         # 設定ファイル
│   ├── schedulers/     # 月次実行スケジューラー
│   ├── logs/           # 実行ログ
│   ├── pyproject.toml  # uvプロジェクト設定
│   ├── uv.lock         # 依存関係ロックファイル
│   ├── README.md       # データ収集システム説明
│   └── main.py         # メイン実行スクリプト
├── web-app/            # ②Webアプリケーションフロー
│   ├── backend/        # Django API
│   │   ├── sheets/     # Google Sheets読み取り専用
│   │   ├── portfolio/  # ポートフォリオ管理
│   │   └── requirements.txt
│   └── frontend/       # Vue.js アプリケーション
│       ├── src/
│       │   ├── components/ # Vue コンポーネント
│       │   ├── views/      # ページコンポーネント
│       │   ├── composables/# Composition API
│       │   ├── router/     # ルーティング
│       │   └── utils/      # ユーティリティ
│       └── package.json
├── shared/             # 共通モジュール
│   ├── sheets_config.py # Google Sheets設定
│   └── __init__.py
└── docs/               # ドキュメント
```

## 開発コマンド

### ①データ収集フロー（月次実行）
- **依存関係インストール**: `cd data-collector && uv sync --dev`
- **対話型実行**: `cd data-collector && uv run python main.py`
- **バッチ実行**: `cd data-collector && uv run python main.py 2024 12`

### ②Webアプリケーションフロー

#### フロントエンド（ポート3000）
- **開発サーバー**: `cd web-app/frontend && npm run dev`
- **依存関係インストール**: `cd web-app/frontend && npm install`

#### バックエンド（ポート8000）
- **開発サーバー**: `cd web-app/backend && uv run python manage.py runserver`
- **マイグレーション**: `cd web-app/backend && uv run python manage.py migrate`
- **依存関係インストール**: `cd web-app/backend && uv sync --dev`

### Python環境管理（uvベース）
- **Pythonインストール**: `uv python install 3.12`
- **仮想環境作成**: `uv venv .venv --python 3.12`
- **依存関係同期**: `uv sync --dev`
- **コードチェック**: `uv run ruff check . --fix`
- **型チェック**: `uvx ty check`

### 環境設定
- **環境変数設定**: web-app/backend/.env ファイルで GOOGLE_APPLICATION_CREDENTIALS と SPREADSHEET_ID を設定
- **data-collector/.env**: GOOGLE_APPLICATION_CREDENTIALSのパスをローカル絶対パスに修正
- **シート構成**: ポートフォリオ（銘柄管理）、データ記録（Django backend用）、損益レポート

## 主要コンポーネント（現在の実装状況）

### フロントエンド（ビルド可能・UI改修予定）
- `App.vue` - 統合ダッシュボード（全機能を1ファイルに集約、Router未使用）
  - 保有銘柄一覧と損益表示
  - ポートフォリオ構成円グラフ（パーセンテージ表示）
  - 総損益推移グラフ（期間選択：3ヶ月/6ヶ月/1年/2年/3年/全期間）
  - 銘柄別損益推移グラフ（取得時期ベース・購入タイミング表示）
  - 詳細取引履歴表示（クリック展開）
  - 買い増し対応（複数回購入の平均価格自動計算）
- コンポーネント群（Dashboard.vue, MonthlyReport.vue等）は存在するがApp.vueから未使用
- **ビルド環境**: package.json + tsconfig.json 整備済み、vite build成功確認済み
- **今後**: 証券アプリ/Yahoo Finance風のUI改修予定（PROJECT_PROCEED.md参照）

### バックエンド（実装済み・Cloud Runデプロイ済み）
- `portfolio/services.py` - Google Sheets読み取り＋損益計算（為替分離対応済み）
- `portfolio/views.py` - ポートフォリオ一覧・履歴・銘柄別API（fxImpacts含む）
- `sheets/views.py` - 市場データAPI（計算ロジック整理済み）
- `sheets/report_generator.py` - 月次レポート生成（GoogleSheetsService経由）

### データ収集（完成・為替分離対応済み）
- `data-collector/main.py` - yfinance→Google Sheets書き込み
- 現地通貨価格・為替レート・為替影響額の記録に対応
- 日付形式YYYY-MM-DD統一済み

## データフロー
### ①データ収集フロー（月次実行・独立）
1. **株価データ収集**: data-collector/main.py → yfinance API → 株価データ取得
2. **データ転記**: Google Sheets API → ポートフォリオ・データ記録・損益レポートシート更新
3. **実行方法**: 手動実行またはcron等のスケジューラーで月次自動実行

### ②Webアプリケーションフロー（リアルタイム表示）
1. **データ読み取り**: Google Sheets → Django API → データ取得・加工
2. **フロントエンド表示**: Vue.js → Chart.js → 損益推移・ポートフォリオ可視化
3. **ユーザー操作**: ダッシュボード操作・月次レポート表示・ブログエクスポート

## API エンドポイント
- `GET /api/v1/data/records/` - 市場データ取得
- `GET /api/v1/portfolio/` - ポートフォリオ一覧（保有銘柄・損益）
- `GET /api/v1/portfolio/history/` - 損益推移（チャート用、fxImpacts含む）
- `GET /api/v1/portfolio/stock/{name}/` - 銘柄別詳細履歴
- `POST /api/v1/manual/update/` - 手動価格更新
- `GET /api/v1/portfolio/validate/` - データ品質検証

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
- ClAUDE.mdとREADEME.mdは開発の状況によって定期的に更新をしていくこと
- 開発の問題点や今後の実装目標・計画はPROJECT_PROCEED.mdに加筆・修正して管理しておくこと
- コミットメッセージは日本語で簡潔に書くこと
