# Portfolio Data Collector

投資ポートフォリオの月次データ収集システム

## 概要
yfinance APIを使用して株価データを取得し、Google Sheetsに転記するPythonアプリケーションです。
外国株の為替レート取得にも対応しています。

## インストール

```bash
# uvを使用した依存関係のインストール
uv sync

# 開発用依存関係も含める場合
uv sync --extra dev
```

## 使用方法

```bash
# 対話型実行
uv run python main.py

# バッチ実行（2024年12月のデータを取得）
uv run python main.py 2024 12

# 月次スケジューラー実行
uv run python schedulers/monthly_runner.py
```

## 環境設定
`.env` ファイルで以下を設定：
- `SPREADSHEET_ID`: Google SheetsのID
- `GOOGLE_APPLICATION_CREDENTIALS`: 認証ファイルパス

## 機能
- 株価データ自動取得
- 外貨建て株式の円換算
- Google Sheetsへのデータ転記
- 損益計算とレポート生成
- 月次スケジューラー実行