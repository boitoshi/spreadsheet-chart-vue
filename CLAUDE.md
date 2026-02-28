# 開発ワークフロー

## 全体の流れ

```
[先輩（あなた）] プランを立てる・設計を決める
    ↓ ゴール・完了条件・参照ファイルを渡す
[後輩ちゃん] 実装・テスト作成をこなす
    ↓ 変更ファイル・判断理由・懸念点を報告
[先輩（あなた）] 報告をレビュー・設計意図とのズレを確認
    ↓
[CLI] lint / check / test（トークン消費ゼロ）
```

## 1. 計画フェーズ（プランモード）

**以下のどちらかに当てはまったら必ずプランモードに入る：**

- ステップが 3 つ以上ある
- 設計判断が必要（どの構造にするか、どのファイルを変えるか）

**プランを立てるときにやること：**

- 変更するファイル・方針・完了条件を明文化して曖昧さをゼロにする
- 実装ステップだけでなく、**検証ステップ**（lint / check / test の何を走らせるか）も一緒に計画する
- 途中で想定外の問題が出たら **即作業を止めて再計画**。無理に進めない。

## 2. 後輩ちゃん（サブエージェント）戦略

**積極的に後輩ちゃんを使う理由：**
先輩（あなた）のコンテキストウィンドウをきれいに保つため。
長い処理・大きなログ・並列作業は後輩ちゃんの中に閉じ込める。

**後輩ちゃんに任せること：**

- ファイルの新規作成・編集・リファクタリング
- テストの作成・実行
- リサーチ・コード探索・ドキュメント調査
- 並列で進められる独立したタスク（複数の後輩ちゃんを同時投入してOK）

**後輩ちゃんの使い方のコツ：**

- **1 後輩ちゃん = 1 タスク** で集中させる。複数タスクを混ぜない。
- 複雑な問題には複数の後輩ちゃんを投入して、より多くの計算リソースをかける。
- 後輩ちゃんに返してもらうのは「変更ファイル・判断理由・懸念点」の 3 点セット。

## 3. チェックリスト（毎タスク確認）

1. [ ] プランを先に立てた？（ファイル・方針・完了条件・検証方法）
2. [ ] 後輩ちゃんに委譲した？（1 後輩ちゃん = 1 タスク）
3. [ ] 後輩ちゃんの報告をレビューした？
4. [ ] `npm run lint` を実行した？
5. [ ] `npm run check` を実行した？

## 4. CLI で直接やること（後輩ちゃん不要）

```bash
npm run lint      # Lint
npm run lint:fix  # Lint 自動修正
npm run format    # Prettier
npm run check     # 型チェック
npm run test      # テスト
```

---

# モデル設定

| 用途                           | モデル               |
| ------------------------------ | -------------------- |
| プラン作成・レビュー・設計判断 | Sonnet 4.6（あなた） |
| 1M コンテキストが必要なとき    | Opus 4.6             |
| 実装タスク（後輩ちゃん）       | `model: sonnet`      |
| 単純作業（後輩ちゃん）         | `model: haiku`       |

---

# プロジェクト設定

## 概要

Vue.js + Django による投資ポートフォリオ管理アプリケーション。Google Sheetsと連携し、資産管理・月次レポート生成・チャート表示を行う。

## 技術スタック

- **フロントエンド**: Vue.js 3, Vue Router, Chart.js, Vite
- **バックエンド**: Django, Google Sheets API, uv（パッケージ管理）
- **Pythonツールチェーン**: uv, ruff, ty（すべてAstral社製）
- **言語**: TypeScript/Vue.js（フロント）, Python 3.12（バック）

## 開発コマンド

```bash
# データ収集（月次実行）
cd data-collector && uv sync --dev
cd data-collector && uv run python main.py          # 対話型
cd data-collector && uv run python main.py 2024 12  # バッチ

# フロントエンド（ポート3000）
cd web-app/frontend && npm run dev

# バックエンド（ポート8000）
cd web-app/backend && uv run python manage.py runserver
cd web-app/backend && uv run python manage.py migrate

# Python品質チェック（各プロジェクトディレクトリで実行）
uv run ruff check . --fix
uvx ty check
```

## 環境設定

- `data-collector/.env`: `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`
- `web-app/backend/.env`: `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `DEBUG=False`, `SECRET_KEY`

## 実装状況

| 層 | 状態 |
|---|---|
| data-collector | 完成（yfinance→Sheets書き込み・ブログ生成） |
| Django sheets/ | 実装済み（portfolio/currency/manual-update） |
| Django portfolio/, reports/ | views.py 未実装 |
| フロントエンド | API連携コード有り（`/api/v1/portfolio/` が未実装） |

## 開発ガイドライン

- コードコメント・コミットメッセージ・会話はすべて日本語
- CLAUDE.md・README.md は開発状況に合わせて随時更新する
- 開発の問題点・実装計画は `PROJECT_PROCEED.md` で管理する
- コンポーネントは単一責任の原則・Composition API を活用

---

# 詳細ドキュメント

@docs/project-structure.md
@docs/sheets-schema.md
@docs/api-reference.md
