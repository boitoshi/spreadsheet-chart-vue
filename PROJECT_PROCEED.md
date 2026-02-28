# プロジェクト進行状況と今後の計画

---

## 2026-02-28: ドキュメント整備・静的解析修正

### 実施内容

- **CLAUDE.md 分割**: 268行の単一ファイルを `@import` 形式で4ファイルに分割（138行に削減）
  - `docs/project-structure.md` — ディレクトリ構成・データフロー
  - `docs/sheets-schema.md` — スプレッドシートカラム定義・損益計算式
  - `docs/api-reference.md` — 実装済み/未実装エンドポイント一覧
- **`data-collector/pyproject.toml` 修正**: `[tool.ty]` の `python-version` を `[tool.ty.environment]` 以下に移動。`extra-paths` で `collectors/`・`config/`・`../shared/` を追加
- **`data-collector/main.py` インポート修正**: `sys.path.append` + フラットインポートを、パッケージ形式（`from collectors.xxx import yyy`、`from config.settings import yyy`）に変更。ruff・ty・IDE 警告がすべてゼロに
- **ルート `pyproject.toml` 修正**: VS Code が参照するルートの `[tool.ty.environment]` に `python-version` と `extra-paths = ["shared"]` を追加
- **`web-app/backend/README.md`**: ほぼ空だったファイルに起動手順・エンドポイント一覧・ディレクトリ構成を記述

---

## 2026-02-28: コードベース評価サマリー

### 実装状況

| 層 | 状態 | 詳細 |
|---|---|---|
| data-collector | 完成 | yfinance→Sheets書き込み・ブログ生成まで動作 |
| バックエンド（Django） | 部分実装 | sheets/ 実装済み、portfolio/reports 未実装 |
| フロントエンド（Vue.js） | 実装中 | API連携コード有り、ダミーデータ残存あり |

### 発見した問題（優先度順）

#### 高優先度（本番化前に必須）
- [ ] `web-app/backend/backend/settings.py` L26: `DEBUG` デフォルトが `True` → `False` に変更
- [ ] `web-app/backend/backend/settings.py` L124: `CORS_ALLOW_ALL_ORIGINS` のデフォルト値見直し
- [ ] `web-app/backend/sheets/views.py` L14: 裸の `except` による例外隠蔽を修正
- [ ] フロントエンド `api.js` L94 が呼ぶ `/api/v1/portfolio/` エンドポイントを実装

#### 中優先度
- [ ] `get_gspread_client()` が `manual_updater.py` と `report_generator.py` で重複 → `shared/` に移動
- [ ] `sheets/views.py` の全関数に型ヒント追加
- [ ] `report_generator.py` L324, L342 のダミーデータ（前月比・月次トピックス）実装

#### 低優先度
- [ ] `App.vue`（783行）のコンポーネント分割（Pinia 導入も検討）
- [ ] `api.js`, `composables/` を TypeScript に移行
- [ ] yfinance API 呼び出しにリトライ・レート制限実装

### 次のアクション

1. `portfolio/` アプリに `views.py` を実装（`/api/v1/portfolio/` エンドポイント）
2. フロントエンドの為替損益表示対応（App.vue）
3. `DEBUG=False` / `CORS_ALLOW_ALL_ORIGINS=False` を本番デフォルトに

---

## 2025年7月20日完了済み項目

### ✅ 時系列精度向上（重要）
- **時系列を正確に考慮した損益計算ロジック完成**: 取得時期以前の期間での損益計算を排除し、webサイト公開レベルの正確性を実現
- **銘柄別表示期間制御の実装**: 個別銘柄選択時に取得開始時期以降のデータのみ表示
- **データ品質保証と妥当性検証機能**: 包括的なデータ検証とリアルタイム品質監視

### 🔧 技術実装完了
- Django Cloud Run デプロイメント完成
- Google Sheets API 統合とエラーハンドリング
- Vue.js フロントエンドとCloud Run バックエンドの連携
- 3ライン表示チャート（取得価格・評価額・損益推移）

## ⚠️ 現在の課題（次回優先対応）

### 🚨 高優先度
1. **総損益推移の全銘柄統合**: 現在は任天堂のみ、DeNAとエヌビディアも含める必要あり
2. **銘柄別損益推移グラフ非表示問題**: 個別銘柄選択時にグラフが表示されない

### 📊 中優先度  
3. **フロントエンドでの個別銘柄データ取得**: 新しいAPIエンドポイントとの完全連携
4. **全銘柄統合チャートのパフォーマンス最適化**

## 🔍 既存の構成課題

### 1. 構成の課題
- バックエンドとフロントエンドが同階層で分かりにくい
- テンプレートとドキュメントの配置が散らばっている
- 環境設定ファイルの管理が複雑

### 2. ファイル管理の課題
- 重複するコンポーネント（LineChart2.vue, Spreadsheet2.vue）
- 不要なREADME.mdファイル
- サンプルファイル（hello.py）の残存

## 🎯 最適化提案

### プロポーザル A: モノレポ構成（推奨）
```
portfolio-tracker/
├── apps/                           # アプリケーション本体
│   ├── frontend/                   # Vue.js アプリ
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── charts/         # チャート系コンポーネント
│   │   │   │   │   ├── LineChart.vue
│   │   │   │   │   └── ProfitChart.vue
│   │   │   │   ├── portfolio/      # ポートフォリオ系
│   │   │   │   │   ├── PortfolioDashboard.vue
│   │   │   │   │   ├── StockTable.vue
│   │   │   │   │   └── Spreadsheet.vue
│   │   │   │   ├── export/         # エクスポート系
│   │   │   │   │   └── BlogExport.vue
│   │   │   │   └── ui/             # 共通UI
│   │   │   │       ├── Button.vue
│   │   │   │       ├── Modal.vue
│   │   │   │       └── Loading.vue
│   │   │   ├── views/              # ページコンポーネント
│   │   │   ├── composables/        # ビジネスロジック
│   │   │   ├── services/           # API通信
│   │   │   ├── types/              # TypeScript型定義
│   │   │   └── assets/
│   │   ├── public/
│   │   └── tests/                  # テストファイル
│   └── backend/                    # Django API
│       ├── config/                 # Django設定
│       │   ├── settings/
│       │   │   ├── base.py
│       │   │   ├── development.py
│       │   │   └── production.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       ├── apps/                   # Django アプリ
│       │   ├── portfolio/          # ポートフォリオ管理
│       │   │   ├── models.py
│       │   │   ├── views.py
│       │   │   ├── serializers.py
│       │   │   └── urls.py
│       │   ├── reports/            # レポート生成
│       │   │   ├── models.py
│       │   │   ├── views.py
│       │   │   ├── generators.py
│       │   │   └── urls.py
│       │   └── sheets/             # Google Sheets連携
│       │       ├── services.py
│       │       ├── updater.py
│       │       └── views.py
│       ├── templates/              # HTMLテンプレート
│       └── tests/
├── tools/                          # 開発・運用ツール
│   ├── scripts/                    # 便利スクリプト
│   │   ├── setup.sh
│   │   ├── deploy.sh
│   │   └── backup.sh
│   ├── docker/                     # Docker設定
│   │   ├── Dockerfile.frontend
│   │   ├── Dockerfile.backend
│   │   └── docker-compose.yml
│   └── ci/                         # CI/CD設定
├── shared/                         # 共通リソース
│   ├── types/                      # TypeScript型定義
│   ├── constants/                  # 定数
│   └── utils/                      # 共通ユーティリティ
├── docs/                           # ドキュメント
│   ├── api/                        # API仕様書
│   ├── guides/                     # 利用ガイド
│   ├── archives/                   # 月次レポートアーカイブ
│   │   └── reports/
│   │       ├── 2024/
│   │       └── templates/
│   └── assets/                     # ドキュメント用画像
├── config/                         # プロジェクト設定
│   ├── .env.example
│   ├── .gitignore
│   └── package.json               # workspace設定
└── README.md
```

### プロポーザル B: シンプル構成（現行改善版）
```
portfolio-tracker/
├── client/                         # フロントエンド
│   ├── src/
│   │   ├── components/
│   │   │   ├── chart/             # チャート関連
│   │   │   ├── portfolio/         # ポートフォリオ関連
│   │   │   ├── report/            # レポート関連
│   │   │   └── common/            # 共通コンポーネント
│   │   ├── pages/                 # ページ（views → pages）
│   │   ├── hooks/                 # composables → hooks
│   │   ├── api/                   # サービス層
│   │   └── utils/
│   └── public/
├── server/                         # バックエンド
│   ├── core/                      # Django設定
│   ├── api/                       # APIアプリ
│   │   ├── portfolio/
│   │   ├── reports/
│   │   └── sheets/
│   └── templates/
├── shared/                         # 共通
│   ├── types/
│   └── constants/
├── docs/
│   ├── reports/                   # アーカイブ
│   └── guides/
├── scripts/                       # ユーティリティ
└── config/                        # 設定ファイル
```

## 🔧 実装手順

### Phase 1: 基本清理
- [x] 重複ファイルの削除（LineChart2.vue, Spreadsheet2.vue）
- [x] 不要ファイルの削除（各README.md, hello.py）
- [x] .gitignoreの統合とルート移動

### Phase 2: コンポーネント整理（推奨）
```bash
# フロントエンド構造変更
mkdir -p frontend/src/components/{charts,portfolio,export,ui}
mv frontend/src/components/LineChart.vue frontend/src/components/charts/
mv frontend/src/components/ProfitChart.vue frontend/src/components/charts/
mv frontend/src/components/PortfolioDashboard.vue frontend/src/components/portfolio/
mv frontend/src/components/StockTable.vue frontend/src/components/portfolio/
mv frontend/src/components/Spreadsheet.vue frontend/src/components/portfolio/
mv frontend/src/components/BlogExport.vue frontend/src/components/export/
```

### Phase 3: バックエンド構造変更
```bash
# Django アプリの分割
cd backend
python manage.py startapp portfolio
python manage.py startapp reports
# 既存のsheets_apiをsheetsにリネーム
```

### Phase 4: 設定ファイルの整理
```bash
# 設定ディレクトリの作成
mkdir config
mv .env.example config/
# workspace package.json作成（モノレポの場合）
```

## 📊 比較表

| 項目 | 現在 | プロポーザルA | プロポーザルB |
|------|------|---------------|---------------|
| 理解しやすさ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 保守性 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| スケーラビリティ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 移行コスト | - | ⭐⭐ | ⭐⭐⭐⭐ |
| チーム開発 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🎯 推奨案

**プロポーザル A（モノレポ構成）** を推奨します。

### 理由
1. **明確な責任分離**: フロントエンド・バックエンドの境界が明確
2. **機能別整理**: コンポーネントが機能ごとに整理される
3. **拡張性**: 新機能追加時の構造が明確
4. **保守性**: ファイルの場所が予測しやすい
5. **チーム開発**: 複数人での開発に適している

### 次のステップ
1. コンポーネントの機能別分類実装
2. バックエンドのアプリケーション分割
3. 共通設定ファイルの整理
4. ドキュメントの再構成

## 🚨 注意点

- **段階的移行**: 一度に全てを変更せず、段階的に実装
- **import文の更新**: ファイル移動に伴うimport文の修正が必要
- **テストの更新**: ファイルパス変更に伴うテスト修正
- **CI/CDの調整**: ビルドパスの変更が必要

---

どちらの提案も現在の構成より大幅に改善されます。プロジェクトの規模と将来性を考慮して選択してください。

---

## 2026-02-06: Docker/devcontainerからローカル開発環境への移行

### 実施内容
- devcontainer環境を削除し、ローカル開発環境に完全移行
- **uv一本でPythonバージョン管理** - pyenv不要
- **型チェッカーをtyに変更** - Astral社製の超高速型チェッカー（ruff + ty）
- uvワークスペース + npm によるハイブリッド構成
- VS Code設定（settings/tasks/launch.json）の移行
- README.md, CLAUDE.md の更新

### 削除したファイル
- `.devcontainer/` ディレクトリ全体

### 技術スタック（移行後）
- **Python管理**: uv（バージョン管理含む）
- **Python型チェック**: ty（Astral社製、mypyの代替）
- **Python リンター/フォーマッター**: ruff
- **Node.js**: npm（バージョン管理はnvm推奨だが任意）
- **開発環境**: VS Code（ローカルネイティブ）
- **デプロイ**: Docker（本番用Dockerfileは維持）

### 重要な変更点
- `pyproject.toml` - mypyからtyに変更、ルートプロジェクトからbuild-systemを削除
- `data-collector/.env` - GOOGLE_APPLICATION_CREDENTIALSのパスをdevcontainer用からローカル絶対パスに変更
- `.vscode/` - settings.json, tasks.json, launch.jsonを新規作成・更新

### 今後の課題
- [ ] CI/CDパイプラインでのuvとPython 3.12バージョン統一
- [ ] 本番Dockerfileの定期的なメンテナンス
- [ ] チーム開発時の.vscode設定共有方法検討
- [ ] tyの言語サーバー統合（VS Code拡張機能が利用可能になった場合）

---

## 2026-02-07: 外国株の外貨建て取得単価・取得時為替レート記録機能

### 実施内容
- ポートフォリオシートに「取得単価（外貨）」「取得時為替レート」カラムを追加（10→12カラム）
- 損益レポートシートに「通貨」「取得単価（外貨）」「月末価格（外貨）」「取得時為替レート」「現在為替レート」カラムを追加（11→16カラム）
- `shared/sheets_config.py` のヘッダー定義を統一（sheets_writer.pyとの矛盾を解消）
- 為替損益と株価損益の分離計算ロジックを実装
- `pyproject.toml` に ty（Astral社製型チェッカー）を依存関係として追加

### 変更ファイル
- `shared/sheets_config.py` - HEADERS/COLUMN_RANGES/SHEET_NAMES統一
- `data-collector/config/settings.py` - DEFAULT_STOCKSに外貨情報追加
- `data-collector/collectors/stock_collector.py` - 損益分離計算（株価損益/為替損益）
- `data-collector/collectors/sheets_writer.py` - sheets_configからヘッダー参照、12/16カラム対応
- `data-collector/main.py` - 外貨カラム読み取り・書き込み拡張
- `data-collector/collectors/report_generator.py` - ブログレポートに外貨・為替損益情報追加
- `web-app/backend/sheets/currency_views.py` - A1:L範囲拡張、外貨情報レスポンス追加
- `web-app/backend/portfolio/services.py` - 外貨建て加重平均計算、Vue.js形式に通貨情報追加
- `data-collector/pyproject.toml` - ty依存追加
- `web-app/backend/pyproject.toml` - ty依存追加

### 損益分離計算式
- 株価損益 = (月末外貨価格 - 取得外貨価格) × 取得時為替レート × 株数
- 為替損益 = (現在為替レート - 取得時為替レート) × 月末外貨価格 × 株数
- 総損益 = 株価損益 + 為替損益（= 評価額 - 取得額）

### ポートフォリオシート設計変更
- D列（取得単価（円））を数式 `=K*L` に変更（外貨単価×為替レートから自動算出）
- K列（取得単価（外貨））とL列（取得時為替レート）が入力元
- 日本株: K=円建て価格, L=1.0 → D=K*L
- 外国株: K=外貨価格, L=取得時レート → D=K*L（円換算）
- 通貨コードはISO形式（JPY, USD, HKD）

### スプレッドシートマイグレーション（完了）
- [x] K-L列のヘッダー追加（取得単価（外貨）、取得時為替レート）
- [x] 外国株のK/L列にデータ入力（楽天証券の保有数量明細から取得）
- [x] D列を `=K*L` 数式に変更
- [x] 通貨コード入力（JPY/USD/HKD）
- [x] 外国株フラグ（○）設定
- [x] `uv sync --dev` で ty インストール確認
- [x] `uv run python main.py 2025 1` で動作確認（NVDA為替損益分離が正常動作）

### 後方互換性
- D列が空の場合、K*Lから自動算出（main.pyのフォールバック）
- K/L列が空の場合、D列の値をそのまま使用（為替レート=1.0）
- 必須フィールド（銘柄コード、銘柄名、保有株数）が空の行は自動スキップ

### main.py バグ修正
- `except ValueError` が引数パースだけでなく `collect_monthly_data` 内部エラーも隠蔽していた問題を修正
- 必須フィールド（銘柄コード、銘柄名、保有株数）が空の行をスキップするバリデーション追加

### 損益レポートの保有期間フィルタリング（2026-02-07追加）
- ポートフォリオの「取得日」を参照し、取得月以降のみ損益レポートに記録
- 取得前の期間はデータ記録（市場データ）のみ記録し、損益計算は行わない
- `--range`で過去データを一括取得した際、保有していない期間の不正な損益レコードが作成されなくなった
- 取得日が空の場合はデフォルトで保有扱い（後方互換性）

### 今後の課題
- [ ] フロントエンドでの為替損益表示対応（App.vue）
- [ ] フロントエンドのapi.jsに為替API呼び出し関数を追加