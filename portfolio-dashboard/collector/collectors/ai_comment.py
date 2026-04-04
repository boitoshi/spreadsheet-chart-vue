"""Claude Haiku を使った月次投資ブログ用AIコメント生成モジュール"""

from __future__ import annotations

import anthropic


class AiCommentGenerator:
    """Claude Haiku による月次投資ブログコメント生成クラス"""

    MODEL = "claude-haiku-4-5-20251001"

    def __init__(self) -> None:
        """初期化。ANTHROPIC_API_KEY 環境変数を自動読み込み。"""
        self.client = anthropic.Anthropic()

    def generate_stock_comment(self, stock_data: dict) -> str:
        """個別銘柄の2〜3文コメントを生成する。

        Args:
            stock_data: 銘柄データ辞書。以下のキーを持つ:
                - name: 銘柄名
                - symbol または code: ティッカーコード
                - current_price: 現在価格
                - pl: 損益額
                - pl_rate: 損益率 (%)
                - market_data: {"change_rate": 月間変動率(%)}
                - currency: 通貨コード（JPY / USD 等）

        Returns:
            生成されたコメント文字列。失敗時は「（コメント生成をスキップ）」。
        """
        symbol = stock_data.get("symbol") or stock_data.get("code", "")
        name = stock_data.get("name", "")
        current_price = stock_data.get("current_price", 0)
        pl = stock_data.get("pl", 0)
        pl_rate = stock_data.get("pl_rate", 0)
        currency = stock_data.get("currency", "JPY")
        market_data = stock_data.get("market_data") or {}
        change_rate = market_data.get("change_rate", 0)

        prompt = (
            f"銘柄: {name}（{symbol}）\n"
            f"現在価格: {current_price:,} {currency}\n"
            f"損益: {pl:+,.0f} {currency}（{pl_rate:+.2f}%）\n"
            f"今月の値動き: {change_rate:+.2f}%\n\n"
            "この銘柄について、個人投資家の視点で2〜3文のコメントを書いてください。"
            "数値に言及しつつ、読者が共感できる自然な文体でお願いします。"
        )

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=300,
                system=(
                    "あなたは個人投資家のブログ筆者です。"
                    "月次の投資成績をブログに記録しています。"
                    "読者に向けて、投資の結果を率直かつ親しみやすい言葉で伝えてください。"
                    "箇条書きや見出しは使わず、自然な文章のみで回答してください。"
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            text_block = next(
                (b for b in response.content if b.type == "text"), None
            )
            if text_block:
                return text_block.text.strip()
            return "（コメント生成をスキップ）"
        except Exception:  # noqa: BLE001
            return "（コメント生成をスキップ）"

    def generate_summary(self, portfolio_data: dict) -> str:
        """ポートフォリオ全体の3〜5文サマリーを生成する。

        Args:
            portfolio_data: ポートフォリオデータ辞書。以下のキーを持つ:
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - holdings: 保有銘柄リスト（各要素は generate_stock_comment と同形式）

        Returns:
            生成されたサマリー文字列。失敗時は「（コメント生成をスキップ）」。
        """
        total_value = portfolio_data.get("total_value", 0)
        total_pl = portfolio_data.get("total_pl", 0)
        total_pl_rate = portfolio_data.get("total_pl_rate", 0)
        holdings = portfolio_data.get("holdings", [])

        holdings_lines = []
        for h in holdings:
            symbol = h.get("symbol") or h.get("code", "")
            name = h.get("name", "")
            pl_rate = h.get("pl_rate", 0)
            holdings_lines.append(f"  - {name}（{symbol}）: {pl_rate:+.2f}%")
        holdings_text = (
            "\n".join(holdings_lines) if holdings_lines else "  （保有銘柄なし）"
        )

        prompt = (
            f"今月のポートフォリオ全体成績:\n"
            f"  合計評価額: {total_value:,.0f} 円\n"
            f"  総損益: {total_pl:+,.0f} 円（{total_pl_rate:+.2f}%）\n\n"
            f"保有銘柄別損益率:\n{holdings_text}\n\n"
            "ポートフォリオ全体について、個人投資家の視点で3〜5文のまとめコメントを書いてください。"
            "良かった点・反省点・来月への展望を含めて、読者が共感できる自然な文体でお願いします。"
            "箇条書きや見出しは使わず、自然な文章のみで回答してください。"
        )

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=500,
                system=(
                    "あなたは個人投資家のブログ筆者です。"
                    "月次の投資成績をブログに記録しています。"
                    "読者に向けて、ポートフォリオ全体の振り返りを率直かつ親しみやすい言葉で伝えてください。"
                    "箇条書きや見出しは使わず、自然な文章のみで回答してください。"
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            text_block = next(
                (b for b in response.content if b.type == "text"), None
            )
            if text_block:
                return text_block.text.strip()
            return "（コメント生成をスキップ）"
        except Exception:  # noqa: BLE001
            return "（コメント生成をスキップ）"

    def generate_all(self, report_data: dict) -> dict:
        """全銘柄コメントとサマリーをまとめて生成する。

        Args:
            report_data: レポートデータ辞書。以下のキーを持つ:
                - holdings: 保有銘柄リスト
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)

        Returns:
            {
                "stock_comments": {ティッカーコード: コメント文字列, ...},
                "summary": サマリー文字列,
            }
        """
        holdings = report_data.get("holdings", [])

        stock_comments: dict[str, str] = {}
        for holding in holdings:
            symbol = holding.get("symbol") or holding.get("code", "")
            comment = self.generate_stock_comment(holding)
            stock_comments[symbol] = comment

        portfolio_data = {
            "total_value": report_data.get("total_value", 0),
            "total_pl": report_data.get("total_pl", 0),
            "total_pl_rate": report_data.get("total_pl_rate", 0),
            "holdings": holdings,
        }
        summary = self.generate_summary(portfolio_data)

        return {"stock_comments": stock_comments, "summary": summary}
