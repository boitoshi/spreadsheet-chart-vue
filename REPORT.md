# 夜間タスク報告（2026-09-14）

## 対応した指摘

1. AI コメント生成失敗の無音フォールバックを修正（`e315ec1`）
   - API 例外の種類、JSON 解析・構造エラー、intro と銘柄ごとの検証失敗理由を標準出力に表示するようにした。
   - intro と各銘柄を独立に検証し、検証に落ちた項目だけを除外するようにした。intro が落ちても有効な銘柄コメントは残す。intro は銘柄カードと独立した標準ブロックであり、他の有効な出力を捨てる必要がないためこの扱いとした。
   - 全項目が空の場合は両方の `main.py` 経路で警告し、DB 保存をスキップする。これにより通常の再実行で再生成できる。
   - 部分成功を DB に保存した場合も、intro と対象銘柄がすべて揃うまでは次回実行で再生成するようにした。
2. フォールバックテストの名前と条件を一致（`d480826`）
   - `current_price=None` を使う重複した不正 JSON テストを、モック API が `RuntimeError` を投げるテストに置き換えた。
3. 関連リンクの削除を確認
   - 指示どおりコードは変更していない。現行テンプレートに「ポートフォリオの全体像」と「この月のデータを見る」がなく、テストが内部リンクの非存在を検証していることを確認した。

## テスト結果

`portfolio-dashboard/collector` で実行した。

- `UV_CACHE_DIR=/tmp/portfolio-dashboard-uv-cache uv run pytest`: 成功（78 passed）
- `UV_CACHE_DIR=/tmp/portfolio-dashboard-uv-cache uv run ruff check .`: 成功
- `UV_CACHE_DIR=/tmp/portfolio-dashboard-uv-cache uv run ty check`: 失敗（8 diagnostics）
  - `collectors/stock_collector.py:83-89` の pandas 列に対する `iloc` / `max` / `min` / `mean` の型診断 6 件
  - `main.py:212` の Optional な `output_path` を `open` に渡す型診断 1 件
  - `main.py:370` の `object` を `float` に渡す型診断 1 件
  - 今回の変更で新たに発生した型診断は解消済み。上記は変更前からある箇所のため、指示どおり修正していない。

server / client は変更していないため、npm の lint / check / test は実行していない。

## 人間の判断待ち

- `templates/blog_template.md` から「ポートフォリオの全体像」（`/pokemon-investment-portfolio/`）と「この月のデータを見る」を削除した意図の確認が必要。

## 人間がやること

- 別リポジトリ `pokebros-blog-manager` の `articles/pokemon-investment-202608.html` にある未コミットの書き戻し結果を確認し、必要に応じてコミットする。
- 同リポジトリの `tasks/global.md` T-001 を更新する。生成器の正本を `080ddb3` にし、記事構成の説明を現在の分割後構成に合わせる。
