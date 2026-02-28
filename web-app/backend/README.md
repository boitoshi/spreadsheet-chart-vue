# Django バックエンド API

Google Sheets連携の投資ポートフォリオ管理 Django REST API。

## 技術スタック

- Django + Django REST Framework
- Google Sheets API（gspread）
- Python 3.12 / uv（パッケージ管理）
- ruff（リンター）/ ty（型チェッカー）

## 起動方法

```bash
cd web-app/backend
uv sync --dev

# 開発サーバー（ポート8000）
uv run python manage.py runserver

# マイグレーション（初回）
uv run python manage.py migrate
```

## 環境変数

`.env` ファイルを `web-app/backend/` に作成：

```env
SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
DEBUG=False
SECRET_KEY=your-secret-key
```

## API エンドポイント

| メソッド | パス | 説明 | 実装状態 |
|---------|------|------|---------|
| GET | `/api/portfolio/` | ポートフォリオ一覧・損益データ | 実装済み |
| GET | `/api/portfolio/history/` | 損益推移履歴 | 実装済み |
| GET | `/api/currency/` | 為替レート | 実装済み |
| POST | `/api/manual-update/` | 手動データ更新 | 実装済み |
| GET | `/api/v1/portfolio/` | フロントエンドからの呼び出し | **未実装** |

## ディレクトリ構成

```
backend/
├── backend/              # Django プロジェクト設定
│   ├── settings.py
│   └── urls.py
├── sheets/               # Google Sheets API 連携（実装済み）
│   ├── views.py           # ポートフォリオ・損益履歴API
│   ├── currency_views.py  # 為替レートAPI
│   ├── manual_updater.py  # 手動更新API
│   └── report_generator.py
├── portfolio/            # ポートフォリオアプリ（views.py 未実装）
├── reports/              # レポートアプリ（views.py 未実装）
└── manage.py
```

## コード品質チェック

```bash
uv run ruff check . --fix
uvx ty check
```

## 注意事項

- Google サービスアカウント JSON が必要（GCP コンソールで発行）
- スプレッドシートにサービスアカウントのメールアドレスを共有設定すること
- 本番環境では必ず `DEBUG=False` を設定
- `portfolio/` と `reports/` アプリは views.py が未実装
