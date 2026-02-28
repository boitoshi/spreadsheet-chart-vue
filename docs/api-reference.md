# API リファレンス

Django バックエンド（ポート8000）のエンドポイント一覧。

## 実装済み

| メソッド | パス | 説明 | 実装ファイル |
|---------|------|------|------------|
| GET | `/api/portfolio/` | ポートフォリオ一覧・損益データ | `sheets/views.py` |
| GET | `/api/portfolio/history/` | 損益推移履歴 | `sheets/views.py` |
| GET | `/api/currency/` | 為替レート | `sheets/currency_views.py` |
| POST | `/api/manual-update/` | 手動データ更新 | `sheets/manual_updater.py` |

## 未実装（フロントエンドから呼び出し中）

| メソッド | パス | 呼び出し元 |
|---------|------|-----------|
| GET | `/api/v1/portfolio/` | `web-app/frontend/src/utils/api.js` L94 |

`/api/v1/portfolio/` は `portfolio/` アプリの `views.py` を実装して対応する。

## レスポンス形式

### GET /api/portfolio/

```json
{
  "stocks": [
    {
      "name": "銘柄名",
      "code": "7974.T",
      "currency": "JPY",
      "isForeign": false,
      "transactions": [
        { "date": "2024-01-15", "quantity": 50, "price": 2400 }
      ],
      "currentPrice": 2800,
      "profit": 20000,
      "profitRate": 16.67
    }
  ]
}
```
