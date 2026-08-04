"""Claude Sonnet を使った月次投資ブログ用AIコメント生成モジュール

ハルシネーション対策として、プロンプトには report_generator が構築した
実データ（損益・値動き・ベンチマーク騰落率・為替）のみを渡し、
「与えられた事実のみに言及する」ことをシステムプロンプトで強制する。
対象月は Claude の知識カットオフ以降になるため、ニュースやイベントへの
言及は必ず創作（ハルシネーション）になる。そのため出来事系の話題は
一切扱わない構成にしている。
"""

from __future__ import annotations

import anthropic

# ────────────────────────────────────────────────────────────
# 共通ガード文（システムプロンプトに必ず含める）
# ────────────────────────────────────────────────────────────

# ハルシネーション対策: プロンプトで与えられた事実以外を語らせない
_HALLUCINATION_GUARD = (
    "プロンプトで与えられた数値・事実のみに言及してください。"
    "ニュース・イベント・決算・製品発表など、与えられていない出来事への言及や"
    "推測は一切禁止です（対象月はあなたの知識範囲外であり、"
    "書けば必ず創作＝ハルシネーションになります）。"
    "値動きの理由を断定的に語らないでください。"
)

# 初心者配慮: 専門用語を使う場合は一言で意味を添える
_BEGINNER_GUARD = (
    "含み益・取得単価・騰落率などの投資の専門用語を使う場合は、"
    "一言で意味が伝わる補足を添えてください。"
)

_NO_LIST_GUARD = "箇条書きや見出しは使わず、自然な文章のみで回答してください。"


def _format_market_context(market_context: dict | None) -> str:
    """market_context 辞書をプロンプトに埋め込む事実行のテキストに整形する。

    値が None のキーは行ごと省略する（存在しない事実をプロンプトに書かせない
    ため）。全キーが None、または market_context 自体が無い場合は
    「市況データなし」の旨を返す。

    Args:
        market_context: report_generator.get_monthly_report_data が構築する
            市況辞書（nikkei_change / sp500_change / usdjpy_rate /
            usdjpy_change）。None も許容する。

    Returns:
        プロンプトに埋め込む整形済みテキスト。
    """
    market_context = market_context or {}
    lines: list[str] = []

    nikkei_change = market_context.get("nikkei_change")
    if nikkei_change is not None:
        lines.append(f"  - 日経平均株価: 今月 {nikkei_change:+.2f}%")

    sp500_change = market_context.get("sp500_change")
    if sp500_change is not None:
        lines.append(f"  - S&P500: 今月 {sp500_change:+.2f}%")

    usdjpy_rate = market_context.get("usdjpy_rate")
    usdjpy_change = market_context.get("usdjpy_change")
    if usdjpy_rate is not None:
        rate_line = f"  - USD/JPY: {usdjpy_rate:.2f}円"
        if usdjpy_change is not None:
            rate_line += f"（前月比 {usdjpy_change:+.2f}%）"
        lines.append(rate_line)

    if not lines:
        return "（市況データなし。市況・ベンチマークへの言及はしないこと）"
    return "\n".join(lines)


def _build_stock_prompt(
    stock_data: dict, year: int, month: int, market_context: dict | None
) -> str:
    """個別銘柄コメント用のユーザープロンプトを構築する。

    Args:
        stock_data: generate_stock_comment と同形式の銘柄データ辞書
        year: 対象年
        month: 対象月
        market_context: 市況コンテキスト辞書（None 可）

    Returns:
        Claude に渡すユーザープロンプト文字列
    """
    symbol = stock_data.get("symbol") or stock_data.get("code", "")
    name = stock_data.get("name", "")
    current_price = stock_data.get("current_price", 0)
    pl = stock_data.get("pl", 0)
    pl_rate = stock_data.get("pl_rate", 0)
    currency = stock_data.get("currency", "JPY")
    market_data = stock_data.get("market_data") or {}
    change_rate = market_data.get("change_rate", 0)

    context_text = _format_market_context(market_context)

    return (
        f"銘柄: {name}（{symbol}）\n"
        f"現在価格: {current_price:,} {currency}\n"
        f"損益: {pl:+,.0f} {currency}（{pl_rate:+.2f}%）\n"
        f"今月の値動き: {change_rate:+.2f}%\n"
        f"対象月: {year}年{month}月\n\n"
        f"参考: 今月の市況（記載のない指標には言及しないこと）\n{context_text}\n\n"
        "この銘柄について、以下の構成で2〜4文のコメントを書いてください。\n"
        "① 事実: 今月の値動きと損益状況を、上記の数値のまま述べる。\n"
        "② 解説: 上記の市況（日経平均・S&P500など）と比較して論理的に言える範囲だけ"
        "かみ砕いて説明する（例:「日経平均(+x%)より大きく下げており、"
        "市場全体ではなくこの銘柄固有の動きと言えそう」）。値動きの原因を"
        "断定したり推測したりしないこと。\n"
        "③ 締め: 最後の1文だけ、ポケモンファンとしての軽い推し活トーンにする。"
    )


def _build_summary_prompt(
    portfolio_data: dict, year: int, month: int, market_context: dict | None
) -> str:
    """ポートフォリオ全体サマリー用のユーザープロンプトを構築する。

    Args:
        portfolio_data: generate_summary と同形式のポートフォリオデータ辞書
        year: 対象年
        month: 対象月
        market_context: 市況コンテキスト辞書（None 可）

    Returns:
        Claude に渡すユーザープロンプト文字列
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

    context_text = _format_market_context(market_context)

    return (
        f"今月のポートフォリオ全体成績:\n"
        f"  合計評価額: {total_value:,.0f} 円\n"
        f"  総損益: {total_pl:+,.0f} 円（{total_pl_rate:+.2f}%）\n"
        f"対象月: {year}年{month}月\n\n"
        f"保有銘柄別損益率:\n{holdings_text}\n\n"
        f"参考: 今月の市況（記載のない指標には言及しないこと）\n{context_text}\n\n"
        "以下の構成で3〜4文の振り返りを書いてください。\n"
        "① ポートフォリオ全体の事実（評価額・損益）を述べる。\n"
        "② 上記の市況（日経平均・S&P500・為替）と比較して"
        "論理的に言える範囲だけ触れる。\n"
        "③ 初心者にもわかるよう一言解説を添える。\n"
        "④ 「みなさんもポケモン銘柄へお布施投資しましょう！」的な明るいノリで締める。"
    )


def _build_intro_prompt(
    portfolio_data: dict, year: int, month: int, market_context: dict | None
) -> str:
    """記事導入文用のユーザープロンプトを構築する。

    Args:
        portfolio_data: generate_intro と同形式のポートフォリオデータ辞書
        year: 対象年
        month: 対象月
        market_context: 市況コンテキスト辞書（None 可）

    Returns:
        Claude に渡すユーザープロンプト文字列
    """
    total_value = portfolio_data.get("total_value", 0)
    total_pl = portfolio_data.get("total_pl", 0)
    total_pl_rate = portfolio_data.get("total_pl_rate", 0)

    context_text = _format_market_context(market_context)

    return (
        f"対象月: {year}年{month}月\n"
        f"合計評価額: {total_value:,.0f} 円\n"
        f"総損益: {total_pl:+,.0f} 円（{total_pl_rate:+.2f}%）\n\n"
        f"参考: 今月の市況（記載のない指標には言及しないこと）\n{context_text}\n\n"
        "このポケモン投資ブログの月次レポートの冒頭に使う導入文を2〜3文で書いてください。\n"
        "① 全体の損益と市況（言及できる範囲のみ）を一言で伝える。\n"
        "② ポケモンファンがポケモン関連銘柄に「お布施投資」している雰囲気で、"
        "読者が続きを読みたくなる自然な書き出しにする。"
    )


class AiCommentGenerator:
    """Claude Sonnet による月次投資ブログコメント生成クラス"""

    MODEL = "claude-sonnet-5"

    def __init__(self) -> None:
        """初期化。ANTHROPIC_API_KEY 環境変数を自動読み込み。"""
        self.client = anthropic.Anthropic()

    def generate_stock_comment(
        self,
        stock_data: dict,
        year: int,
        month: int,
        market_context: dict | None = None,
    ) -> str:
        """個別銘柄のポケモン推し活トーンの2〜4文コメントを生成する。

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
            market_context: 市況コンテキスト辞書（report_generator が構築。
                nikkei_change / sp500_change / usdjpy_rate / usdjpy_change）。
                None の場合は市況への言及なしでコメントを生成する。

        Returns:
            生成されたコメント文字列。失敗時は「（コメント生成をスキップ）」。
        """
        prompt = _build_stock_prompt(stock_data, year, month, market_context)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                # Sonnet 5 は thinking がデフォルト有効で max_tokens を思考分も
                # 消費するため、短文生成では明示的に無効化する
                thinking={"type": "disabled"},
                max_tokens=300,
                system=(
                    "あなたはポケモンファンのブロガーです。"
                    "ポケモン関連銘柄（任天堂、DeNAなど）に「推しへのお布施」として投資しています。"
                    "投資は推し活の一環で、利益が出たらラッキーというスタンスです。"
                    f"{_HALLUCINATION_GUARD}"
                    f"{_BEGINNER_GUARD}"
                    f"{_NO_LIST_GUARD}"
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

    def generate_summary(
        self,
        portfolio_data: dict,
        year: int,
        month: int,
        market_context: dict | None = None,
    ) -> str:
        """ポートフォリオ全体のポケモン推し活トーンの3〜4文サマリーを生成する。

        Args:
            portfolio_data: ポートフォリオデータ辞書。以下のキーを持つ:
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - holdings: 保有銘柄リスト（各要素は generate_stock_comment と同形式）
            year: 対象年
            month: 対象月
            market_context: 市況コンテキスト辞書（None 可）

        Returns:
            生成されたサマリー文字列。失敗時は「（コメント生成をスキップ）」。
        """
        prompt = _build_summary_prompt(portfolio_data, year, month, market_context)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                # Sonnet 5 は thinking がデフォルト有効で max_tokens を思考分も
                # 消費するため、短文生成では明示的に無効化する
                thinking={"type": "disabled"},
                max_tokens=500,
                system=(
                    "あなたはポケモンファンのブロガーです。"
                    "ポケモン関連銘柄に「推しへのお布施」として投資しています。"
                    "読者にもお布施投資を薦める明るいトーンで締めくくってください。"
                    f"{_HALLUCINATION_GUARD}"
                    f"{_BEGINNER_GUARD}"
                    f"{_NO_LIST_GUARD}"
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

    def generate_intro(
        self,
        portfolio_data: dict,
        year: int,
        month: int,
        market_context: dict | None = None,
    ) -> str:
        """ポートフォリオ全体の記事導入文（2〜3文）を生成する。

        Args:
            portfolio_data: ポートフォリオデータ辞書。以下のキーを持つ:
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - holdings: 保有銘柄リスト
            year: 対象年
            month: 対象月
            market_context: 市況コンテキスト辞書（None 可）

        Returns:
            生成された導入文字列。失敗時は「（コメント生成をスキップ）」。
        """
        prompt = _build_intro_prompt(portfolio_data, year, month, market_context)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                # Sonnet 5 は thinking がデフォルト有効で max_tokens を思考分も
                # 消費するため、短文生成では明示的に無効化する
                thinking={"type": "disabled"},
                max_tokens=300,
                system=(
                    "あなたはポケモンファンのブロガーです。"
                    "ポケモン関連銘柄に「推しへのお布施」として投資しています。"
                    "読者に対して親しみやすいトーンで記事の導入文を書いてください。"
                    f"{_HALLUCINATION_GUARD}"
                    f"{_BEGINNER_GUARD}"
                    f"{_NO_LIST_GUARD}"
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

        report_data から year / month_num / market_context を取り出して
        各生成メソッドに渡す。market_context が無い report_data でも
        （.get で防御しているため）動作する。

        Args:
            report_data: レポートデータ辞書。以下のキーを持つ:
                - holdings: 保有銘柄リスト
                - total_value: 合計評価額
                - total_pl: 総損益額
                - total_pl_rate: 総損益率 (%)
                - year: 対象年
                - month_num: 対象月（数値）
                - market_context: 市況コンテキスト辞書（省略可）

        Returns:
            {
                "stock_comments": {ティッカーコード: コメント文字列, ...},
                "summary": サマリー文字列,
                "intro": 導入文字列,
            }
        """
        holdings = report_data.get("holdings", [])
        year = report_data.get("year", 0)
        month = report_data.get("month_num", 0)
        market_context = report_data.get("market_context")

        stock_comments: dict[str, str] = {}
        for holding in holdings:
            symbol = holding.get("symbol") or holding.get("code", "")
            comment = self.generate_stock_comment(
                holding, year, month, market_context
            )
            stock_comments[symbol] = comment

        portfolio_data = {
            "total_value": report_data.get("total_value", 0),
            "total_pl": report_data.get("total_pl", 0),
            "total_pl_rate": report_data.get("total_pl_rate", 0),
            "holdings": holdings,
        }
        summary = self.generate_summary(portfolio_data, year, month, market_context)
        intro = self.generate_intro(portfolio_data, year, month, market_context)

        return {"stock_comments": stock_comments, "summary": summary, "intro": intro}
