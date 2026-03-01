# プロジェクト進行状況と今後の計画

---

## 今後の実装ロードマップ

実装優先順位（ユーザー決定 2026-03-01）:

### ✅ 完了（2026-03-01）
- [x] バグ修正: /api/portfolio の totalCost=0 / isForeign=false を修正
- [x] 為替損益分離チャート（`ProfitAreaChart` を積み上げ棒グラフ化）
- [x] アセットアロケーション推移チャート（`AllocationTrendChart` 新規作成）
- [x] 銘柄別パフォーマンス比較（`StockCompareChart` 新規作成）
- [x] 配当・分配金記録（`/api/dividend` + `/dividend` ページ新規作成）
  - ⚠️ スプレッドシートに「配当・分配金」シートの手動作成が必要
- [x] 月次レポート Web プレビュー（`/api/reports` + `/reports` ページ新規作成）
- [x] コードリファクタリング: `_to_float` を `utils.py` に集約、`buildPivotData` を `chartUtils.ts` に集約

### 📋 中優先度
2. **CAGR（年率換算リターン）** — 取得日からの保有期間を考慮した年率リターン表示
3. **ベンチマーク比較** — 日経225 / S&P500 と自ポートフォリオのリターンを並べて表示
4. **通貨エクスポージャーサマリー** — JPY/USD/HKD ごとの評価額・損益率を一覧表示

---

## 2026-02-28 web-app 全面再構築完了

### 変更内容
- Django + Vue.js → FastAPI + Next.js 16 に全面移行
- `web-app/backend/`: FastAPI + gspread（4エンドポイント実装済み）
- `web-app/frontend/`: Next.js 16 + Tailwind v4 + Recharts（4ページ実装済み）
- Tremor は React 19 + Tailwind v4 に非対応のため Recharts に変更

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

