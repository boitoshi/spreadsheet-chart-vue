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
│   ├── backend/            # Django REST API
│   │   ├── sheets/         # Google Sheets連携API（実装済み）
│   │   ├── portfolio/      # ポートフォリオアプリ（views.py 未実装）
│   │   ├── reports/        # レポートアプリ（views.py 未実装）
│   │   ├── backend/        # Django設定・urls.py
│   │   └── pyproject.toml
│   └── frontend/           # Vue.js アプリケーション
│       └── src/
│           ├── App.vue         # 統合ダッシュボード（783行）
│           ├── components/     # Vue コンポーネント
│           ├── composables/    # Composition API（一部 JS）
│           ├── utils/api.js    # APIサービス層
│           └── types/          # TypeScript型定義
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
Django API（web-app/backend/sheets/）
    ↓ JSON
Vue.js（web-app/frontend/src/App.vue）
    ↓ Chart.js
ブラウザ（ポートフォリオダッシュボード）
```

## 保有期間フィルタリングの仕様

- ポートフォリオシートの「取得日」（C列）を参照
- **取得月以降**のみ損益レポートに記録
- 取得前の期間はデータ記録（市場データ）のみ記録、損益計算は行わない
- 取得日が空の場合はデフォルトで保有扱い（後方互換性）
