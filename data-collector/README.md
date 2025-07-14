# Portfolio Data Collector

投資ポートフォリオの月次データ収集システム

## 概要
yfinance APIを使用して株価データを取得し、Google Sheetsに転記するPythonアプリケーションです。
外国株の為替レート取得、特定シートのみの更新にも対応しています。

## インストール

```bash
# uvを使用した依存関係のインストール
uv sync

# 開発用依存関係も含める場合
uv sync --extra dev
```

## 使用方法

### 対話型実行
```bash
uv run python main.py
```

対話型メニューから以下の機能を選択できます：
1. **月次データ取得・分析（全シート更新）** - 通常の月次データ収集
2. **期間範囲データ取得・分析（全シート更新）** - 複数月のデータを一括収集
3. **特定シート更新** - 個別シートのみの更新
   - 3-1. 為替レートのみ更新
   - 3-2. 市場データのみ更新  
   - 3-3. 損益レポートのみ更新
4. **ポートフォリオサマリー表示** - 指定月の損益サマリー
5. **シート初期化** - 全シートの構造初期化
6. **現在の為替レート表示** - リアルタイム為替レート確認

### コマンドライン実行

#### 基本実行
```bash
# 単月実行（2024年12月のデータを取得）
uv run python main.py 2024 12

# 期間範囲実行（2023年6月〜2025年6月）
uv run python main.py --range 2023 6 2025 6
```

#### 特定シート更新
```bash
# 為替レートのみ更新
uv run python main.py --currency-only

# 市場データのみ更新（2024年12月）
uv run python main.py --market-data 2024 12

# 損益レポートのみ更新（2024年12月）
uv run python main.py --performance 2024 12
```

#### スケジューラー実行
```bash
# 月次スケジューラー実行
uv run python schedulers/monthly_runner.py
```

## 環境設定

`.env` ファイルで以下を設定：
```env
SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## Google Sheetsの構成

### シート構造
- **ポートフォリオシート**: 保有株式の基本情報（銘柄コード、保有株数、取得単価等）
- **データ記録シート**: 市場データ（月末価格、最高値、最安値、出来高等）
- **損益レポートシート**: 計算済み損益データ
- **為替レートシート**: 外貨建て株式用の為替レート履歴

### データフロー
1. **ポートフォリオシート** - 手動で保有株式情報を管理
2. **data-collector** - yfinance APIで株価取得、各シートに保存
3. **Django backend** - Google Sheetsからデータ読み取り、Vue.js用に変換
4. **Vue.js frontend** - ダッシュボード表示

## 機能

### 主要機能
- **株価データ自動取得** - yfinance APIを使用
- **外貨建て株式対応** - 為替レート取得・円換算
- **Google Sheets連携** - データの自動転記・保存
- **損益計算** - 取得コストと現在価格から自動計算
- **期間範囲実行** - 複数月のデータを一括収集

### 特定シート更新機能
- **効率的な部分更新** - 必要なデータのみ更新可能
- **為替レート専用更新** - 毎日の為替レート更新に最適
- **市場データ専用更新** - 株価データのみ更新
- **損益レポート専用更新** - 計算結果のみ更新

### 外貨対応
対応通貨：USD, EUR, GBP, HKD, AUD, CAD, SGD
- 自動為替レート取得（yfinance USDJPY=X等を使用）
- 円換算計算
- 為替レート履歴保存

## 使用例

### 月次データ収集
```bash
# 2024年12月の全データ収集
uv run python main.py 2024 12
```

### 為替レートの毎日更新
```bash
# 為替レートのみ更新（cron等で毎日実行）
uv run python main.py --currency-only
```

### 過去データの一括収集
```bash
# 2年分のデータを一括収集
uv run python main.py --range 2023 1 2024 12
```

### エラー発生時の部分修復
```bash
# 市場データのみ再取得
uv run python main.py --market-data 2024 12

# 損益計算のみ再実行  
uv run python main.py --performance 2024 12
```

## トラブルシューティング

### よくある問題
1. **Google Sheets認証エラー** - サービスアカウントファイルのパスを確認
2. **yfinance API制限** - 期間範囲実行時は自動的に10秒間隔で実行
3. **銘柄コードエラー** - ポートフォリオシートの銘柄コードを確認

### ログ確認
```bash
# ログファイルの確認
tail -f logs/data_collector.log
```