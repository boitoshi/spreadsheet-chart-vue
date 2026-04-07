"""Claude Haiku を使った月次投資ブログ用AIコメント生成モジュール"""

from __future__ import annotations

import anthropic


class AiCommentGenerator:
    """Claude Haiku による月次投資ブログコメント生成クラス"""

    MODEL = "claude-haiku-4-5-20251001"

    def __init__(self) -> None:
        """初期化。ANTHROPIC_API_KEY 環境変数を自動読み込み。"""
        self.client = anthropic.Anthropic()

    def generate_stock_comment(self, stock_data: dict, year: int, month: int) -> str:
        """個別銘柄のポケモン推し活トーンの2〜3文コメントを生成する。

        Args:
            stock_data: 銘柄データ辞書。以下のキーを持つ:
                - name: 銘柄名
                - symbol または code: ティッカーコード
                - current_price: 現在価格
                - pl: 損益額
                - pl_rate: 損益率 (%)
                - market_data: {"change_rate": 月間変動率(%)}
                - currency: 通貨コード（JPY / USD 等）
            year: 対象年
            month: 対象月

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
            f"今月の値動き: {change_rate:+.2f}%\n"
            f"対象月: {year}年{month}月\n\n"
            "この銘柄の今月の値動きについて、ポケモンファンの視点で2〜3文のコメントを書いてください。"
            "対象月のポケモン関連ニュース（新作発表、イベント、決算等）があれば絡めてください。"
        )

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=300,
                system=(
                    "あなたはポケモンファンのブロガーです。"
                    "ポケモン関連銘柄（任天堂、DeNAなど）に「推しへのお布施」として投資しています。"
                    "投資は推し活の一環で、利益が出たらラッキーというスタンスです。"
                    "ポケモン関連のニュースや出来事に絡めてコメントしてください。"
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

    def generate_summary(self, portfolio_data: dict, year: int, month: int) -> str:
        """ポートフォリオ全体のポケモン推し活トーンの3〜4文サマリーを生成する。

        Args:
            portfolio_data: ポートフォリオデータ辞書。以下のキーを持つ:
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - holdings: 保有銘柄リスト（各要素は generate_stock_comment と同形式）
            year: 対象年
            month: 対象月

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
            f"  総損益: {total_pl:+,.0f} 円（{total_pl_rate:+.2f}%）\n"
            f"対象月: {year}年{month}月\n\n"
            f"保有銘柄別損益率:\n{holdings_text}\n\n"
            "ポケモンファンの視点で、今月の振り返りを3〜4文で書いてください。"
            "「みなさんもポケモン銘柄へお布施投資しましょう！」的なノリで締めてください。"
        )

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=500,
                system=(
                    "あなたはポケモンファンのブロガーです。"
                    "ポケモン関連銘柄に「推しへのお布施」として投資しています。"
                    "読者にもお布施投資を薦める明るいトーンで締めくくってください。"
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

        report_data から year / month_num を取り出して各生成メソッドに渡す。

        Args:
            report_data: レポートデータ辞書。以下のキーを持つ:
                - holdings: 保有銘柄リスト
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - year: 対象年
                - month_num: 対象月（数値）

        Returns:
            {
                "stock_comments": {ティッカーコード: コメント文字列, ...},
                "summary": サマリー文字列,
            }
        """
        holdings = report_data.get("holdings", [])
        year = report_data.get("year", 0)
        month = report_data.get("month_num", 0)

        stock_comments: dict[str, str] = {}
        for holding in holdings:
            symbol = holding.get("symbol") or holding.get("code", "")
            comment = self.generate_stock_comment(holding, year, month)
            stock_comments[symbol] = comment

        portfolio_data = {
            "total_value": report_data.get("total_value", 0),
            "total_pl": report_data.get("total_pl", 0),
            "total_pl_rate": report_data.get("total_pl_rate", 0),
            "holdings": holdings,
        }
        summary = self.generate_summary(portfolio_data, year, month)

        return {"stock_comments": stock_comments, "summary": summary}
