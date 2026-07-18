# portfolio-dashboard 詳細（現行システム）

## ディレクトリ構成

```
portfolio-dashboard/
├── client/                 # Vite + React 19 SPA
│   └── src/
│       ├── pages/          # Dashboard, Portfolio, History, Currency, Dividend, Reports, ReportDetail
│       ├── components/
│       │   ├── dashboard/  # 新デザイン: GradientHeader, SummaryCard, AssetTrendChart,
│       │   │               #   StockCard, StockPriceChart, PeriodToggle, DashboardFooter
│       │   └── report/     # 新デザイン: ReportHeader, ReportSummaryCard, ReportStockCard,
│       │                   #   CtaBox, ReportFooter, ReportMarkdown（旧表示フォールバック）
│       ├── lib/            # api.ts, formatters.ts, chartUtils.ts
│       └── types/          # API レスポンス型
├── server/                 # Hono 4 + Drizzle + better-sqlite3（ポート3000）
│   ├── src/routes/         # dashboard, portfolio, history, currency, dividend, reports, benchmark, exposure
│   ├── src/services/       # reportData.ts（レポートデータビルダー・形状の正）
│   ├── src/db/schema.ts    # Drizzle スキーマ
│   └── drizzle/migrations/ # マイグレーション SQL（IF NOT EXISTS で冪等化済み）
├── collector/              # Python バッチ（uv）
│   ├── main.py             # --sync / --range / --blog / --repair-pnl / --add-purchase / collect_and_publish
│   ├── collectors/         # db_writer, report_generator, ai_comment, wp_publisher,
│   │                       #   block_converter, report_json_builder, embed_generator ほか
│   ├── templates/          # blog_template.md, blog_embed.html（Jinja2）
│   └── output/embeds/      # portfolio_YYYY_MM.json, blog_embed_YYYY_MM(.html/_fragment.html)
├── data/portfolio.db       # SQLite（ローカルは GCS portfolio-backup-pokebros から復元）
└── deploy/                 # Caddyfile, backup.sh 等（GCE）
```

## DB テーブル（server/src/db/schema.ts）

| テーブル | 用途 |
|---|---|
| holdings | 保有銘柄（sheets_sync が DELETE→INSERT 全入替。メタ情報を足さないこと） |
| monthly_prices | 月次価格（円換算）・月間変動率 change_rate |
| monthly_pnl | 銘柄×月の損益。date は `"YYYY-MM-末"` 形式。current_price（円）/ current_price_foreign（外貨）を保持し株価履歴の源泉 |
| exchange_rates | 為替レート（pair `USD/JPY`） |
| purchase_history | 買付履歴（code, seq, shares, price, price_foreign, purchased_at）。移動平均取得単価の源泉 |
| stock_meta | 銘柄カラー・市場表示（7974.T=#E53935/東証プライム、2432.T=#1565C0/東証プライム、NVDA=#76B900/NASDAQ）。未登録銘柄はフォールバック `#FF6F00`→`#7B1FA2` |
| ai_comments | AI コメント永続化（date, code, kind='stock'/'intro'/'summary'）。--blog 再実行時は再利用（AI_COMMENTS_FORCE=true で再生成） |
| dividends / benchmark_data | 配当・ベンチマーク |

## API

| エンドポイント | 備考 |
|---|---|
| GET /api/dashboard | 既存 kpi/allocation/latestProfits ＋ **stocks[]・totalHistory・usdJpy**（新デザイン用。形状の正は `server/src/services/reportData.ts`） |
| GET /api/reports/:year/:month/data | 月次レポートデータ（portfolio.json 形状）。該当月なしは 404 → client は Markdown 表示にフォールバック |
| GET /api/reports/:year/:month | 従来の Markdown レポート（維持） |
| その他 /api/portfolio, /history, /currency, /dividend, /reports, /benchmark, /exposure | 変更なし |

stocks[] の主要フィールド: `currentPrice`/`acquiredPrice`/`priceHistory`/`acquiredAvgHistory` は **native 通貨**（USD 銘柄は外貨）、`value`/`profit` は円建て。`monthLabels` は `"YYYY/M"`。

## デザイン（claude.ai/design 由来）

デザインソース: claude.ai/design プロジェクト「保有株ポートフォリオ可視化アプリ」（ID: 11fbaa01-4d90-470d-91c1-32b30e2766cb）。DesignSync ツールで読み取り可能。

- トークン: 背景 `#f0f2f5`、本文 `#1e2130`、補助 `#8c90a0`、フォント Noto Sans JP。globals.css の `@theme` に定義
- 損益色は日本市場慣習（**プラス=赤 #E53935 / マイナス=青 #1565C0**）。新デザイン部分のみ。旧ページの `profitColor`（緑/赤）は温存
- client 内のチャートは Recharts 統一（Chart.js 禁止）。ブログ埋め込み HTML のみ Chart.js CDN 使用可

## ブログ埋め込みフロー

```
uv run python main.py --blog YYYY MM
  → AI コメント生成（ai_comments テーブルに永続化・既存あれば再利用）
  → report_json_builder が SQLite から portfolio.json を構築
  → templates/blog_embed.html で standalone / fragment の 2 モードをレンダリング
  → output/embeds/ に保存
  → WP_PUBLISH_ENABLED=true なら wp_publisher.create_draft(raw_html_prepend=fragment)
     で WordPress 下書きの先頭に wp:html ブロックとして自動挿入
```

- fragment は全 CSS を `.pf-report-embed` プレフィックスでスコープ済み（テーマ衝突防止）、Chart.js は二重読み込みガード付き動的ロード
- server 側 `reportData.ts` と collector 側 `report_json_builder.py` は同一形状・同一計算。片方を変えたら必ず両方直す

## 買付の記録と monthly_pnl 補正

- 買付入力: `uv run python main.py --add-purchase 7974.T 2026-08-01 1 8500`（日本株）/ `--add-purchase NVDA 2026-08-01 1 208.27 162.35`（外国株: 外貨単価と為替）。シート追記 → holdings/purchase_history 同期 → monthly_pnl 補正まで自動実行。1 株未満の端株（ポケポケサブスク相当の積立分）はポートフォリオ対象外のため受け付けない
- `--repair-pnl [--dry-run]`: monthly_pnl の取得系カラム（shares/cost/acquired_price 系/value/profit）を purchase_history の累積で全月再計算。current_price 系は変更しない。月次収集後にも対象月分が自動補正される（collect_monthly_data 末尾フック）

## GCE デプロイ手順

```bash
# 事前に deploy/backup.sh 相当で DB バックアップを取ること
cd /app && git pull
cd portfolio-dashboard && npm ci && npm run build
npm run db:migrate -w server        # DB: /app/portfolio-dashboard/data/portfolio.db
sudo systemctl restart portfolio
cd collector && uv sync --extra ai --extra charts   # 素の uv sync は extras（anthropic/markdown/matplotlib）を削除してしまう
```

## 旧構成（参考）

`web-app/`（Next.js + FastAPI）・`data-collector/`・`shared/` は 2026-04 の移行前の旧システム。ドキュメントは docs/project-structure.md・docs/sheets-schema.md・docs/api-reference.md（いずれも旧構成の記述）。変更禁止。
