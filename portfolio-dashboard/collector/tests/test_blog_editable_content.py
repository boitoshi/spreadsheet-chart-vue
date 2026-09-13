"""ブログ用埋め込みと編集可能コメントの分離テスト。"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

from collectors import embed_generator as embed_generator_module
from collectors.db_writer import DbWriter
from collectors.embed_generator import EmbedGenerator
from collectors.template_engine import MarkdownTemplateEngine
from collectors.wp_publisher import WpPublisher, compose_monthly_blog_content


class _BalancedTagParser(HTMLParser):
    """wp:htmlセクション内でタグが次のブロックへはみ出していないか調べる。"""

    _VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag not in self._VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        assert self.stack, f"開始タグがない終了タグです: {tag}"
        assert self.stack.pop() == tag


def _assert_balanced_tags(html_content: str) -> None:
    parser = _BalancedTagParser()
    parser.feed(html_content)
    assert parser.stack == []


def _embed_report_data() -> dict:
    return {
        "meta": {
            "year": 2026,
            "month": 8,
            "exchangeRate": 159.73,
            "reportDate": "2026年8月末",
            "purchasesThisMonth": [],
            "isBackfilled": False,
        },
        "intro": "全体コメントのテストです。",
        "summary": "まとめコメントのテストです。",
        "stocks": [
            {
                "code": "7974.T",
                "name": "任天堂",
                "ticker": "7974.T",
                "market": "東証プライム",
                "currency": "JPY",
                "quantity": 1,
                "currentPrice": 9000,
                "previousMonthPrice": 8000,
                "prevMonthChangeRate": 12.5,
                "color": "#E53935",
                "acquiredPrice": 8500,
                "priceHistory": [8000, 9000],
                "acquiredAvgHistory": [8500, 8500],
                "monthLabels": ["2026/7", "2026/8"],
                "purchaseHistory": [],
                "profit": 500,
                "profitRate": 5.88,
                "value": 9000,
                "comment": "個別コメントのテストです。",
            },
            {
                "code": "2432.T",
                "name": "DeNA",
                "ticker": "2432.T",
                "market": "東証プライム",
                "currency": "JPY",
                "quantity": 1,
                "currentPrice": 2500,
                "previousMonthPrice": 2400,
                "prevMonthChangeRate": 4.17,
                "color": "#1565C0",
                "acquiredPrice": 2000,
                "priceHistory": [2400, 2500],
                "acquiredAvgHistory": [2000, 2000],
                "monthLabels": ["2026/7", "2026/8"],
                "purchaseHistory": [],
                "profit": 500,
                "profitRate": 25.0,
                "value": 2500,
                "comment": "DeNAの個別コメントのテストです。",
            },
        ],
        "totalHistory": {
            "labels": ["2026/7", "2026/8"],
            "values": [8000, 9000],
            "profits": [-500, 500],
        },
    }


def _blog_report_data() -> dict:
    return {
        "year": 2026,
        "month_num": 8,
        "prev_month": {
            "year": 2026,
            "month": 7,
            "slug": "pokemon-investment-202607",
        },
        "holdings": [
            {"name": "任天堂", "symbol": "7974.T"},
            {"name": "DeNA", "symbol": "2432.T"},
        ],
        "ai_comments": {
            "intro": "今月の全体コメントです。",
            "stock_comments": {
                "7974.T": "任天堂の個別コメントです。",
                "2432.T": "DeNAの個別コメントです。",
            },
        },
    }


def _render_fragment(engine: MarkdownTemplateEngine) -> str:
    embed_data = _embed_report_data()
    fragment_data = {
        **embed_data,
        "intro": None,
        "summary": None,
        "stocks": [
            {**stock, "comment": None} for stock in embed_data["stocks"]
        ],
    }
    return engine.render(
        "blog_embed.html", {"data": fragment_data, "standalone": False}
    )


def test_embed_generator_separates_editorial_prose(
    tmp_path, monkeypatch
) -> None:
    report_data = _embed_report_data()
    monkeypatch.setattr(
        embed_generator_module,
        "build_report_data",
        lambda _db, _target_date: report_data,
    )
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    generator = EmbedGenerator(
        cast("DbWriter", object()), str(tmp_path), str(template_dir)
    )

    generator.generate(2026, 8)

    standalone = (tmp_path / "embeds" / "blog_embed_2026_08.html").read_text()
    fragment = (
        tmp_path / "embeds" / "blog_embed_2026_08_fragment.html"
    ).read_text()

    assert "全体コメントのテストです。" in standalone
    assert "個別コメントのテストです。" in standalone
    assert "まとめコメントのテストです。" in standalone
    assert "全体コメントのテストです。" not in fragment
    assert "個別コメントのテストです。" not in fragment
    assert "まとめコメントのテストです。" not in fragment
    assert "pokebros-monthly-section" not in standalone
    assert standalone.count('<div class="pf-report-embed">') == 1
    assert standalone.index("pf-combo-chart") < standalone.index("pf-stock-1")
    assert standalone.index("pf-stock-1") < standalone.index("個別コメント")
    _assert_balanced_tags(standalone)


def test_blog_template_makes_comments_editable_and_keeps_fixed_promo() -> None:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    engine = MarkdownTemplateEngine(str(template_dir))

    rendered = engine.render("blog_template.md", _blog_report_data())
    fragment = _render_fragment(engine)
    blocks = compose_monthly_blog_content(rendered, fragment)

    assert "## 今月の振り返り" in rendered
    assert "### 任天堂の振り返り" in rendered
    assert "### DeNAの振り返り" in rendered
    assert "今月の全体コメントです。" in blocks
    assert "任天堂の個別コメントです。" in blocks
    assert "DeNAの個別コメントです。" in blocks
    assert blocks.count("<!-- wp:paragraph -->") >= 3

    html_blocks = re.findall(
        r"<!-- wp:html -->\n(.*?)\n<!-- /wp:html -->", blocks, re.DOTALL
    )
    assert len(html_blocks) == 4
    for html_block in html_blocks:
        _assert_balanced_tags(html_block)
    assert "pokebros-monthly-section" not in blocks
    assert "pf-donut-chart" in html_blocks[0]
    assert 'id="pf-stock-1"' in html_blocks[1]
    assert 'id="pf-stock-2"' in html_blocks[2]
    assert "<script>" in html_blocks[3]
    assert blocks.rstrip().endswith("<!-- /wp:html -->")

    order = [
        blocks.index("pf-combo-chart"),
        blocks.index("今月の全体コメントです。"),
        blocks.index('id="pf-stock-1"'),
        blocks.index("任天堂の振り返り"),
        blocks.index("任天堂の個別コメントです。"),
        blocks.index('id="pf-stock-2"'),
        blocks.index("DeNAの振り返り"),
        blocks.index("DeNAの個別コメントです。"),
        blocks.index("関連リンク"),
        blocks.rindex("<script>"),
    ]
    assert order == sorted(order)
    assert (
        "<!-- wp:paragraph -->\n<p>任天堂の個別コメントです。</p>"
        "\n<!-- /wp:paragraph -->"
    ) in blocks
    assert (
        "<!-- wp:paragraph -->\n<p>DeNAの個別コメントです。</p>"
        "\n<!-- /wp:paragraph -->"
    ) in blocks

    assert "https://portfolio.pokebros.net/reports/2026/8" not in rendered
    assert "https://www.pokebros.net/pokemon-investment-portfolio/" in rendered
    assert "https://portfolio.pokebros.net/" in rendered
    assert "https://www.pokebros.net/pokemon-investment-202607/" in rendered
    assert (
        "/category/%e3%83%9d%e3%82%b1%e3%83%a2%e3%83%b3%e6%8a%95%e8%b3%87/"
        in rendered
    )
    assert "1株からポケモン関連銘柄を買うには" in rendered
    assert "直接開設する前に" in rendered
    assert "ハピタス内の証券会社ページから申し込み" in rendered
    assert "最新条件を確認" in rendered
    assert "紹介した側と紹介された側の両方" in rendered
    assert "https://m.hapitas.jp/item/detail/itemid/53979" in rendered
    assert "https://m.hapitas.jp/item/detail/itemid/35520" in rendered
    assert "https://m.hapitas.jp/item/detail/itemid/99234" in rendered
    assert "https://hapitas.jp/appinvite" in rendered
    assert "投資判断はご自身の責任で" in rendered
    assert "ニュース" not in rendered


def test_blog_template_treats_generated_markup_as_plain_text() -> None:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    engine = MarkdownTemplateEngine(str(template_dir))
    report_data = _blog_report_data()
    report_data["ai_comments"]["intro"] = "# 全体はプラスです。"
    report_data["ai_comments"]["stock_comments"]["7974.T"] = (
        "<div>任天堂はプラスです。</div>"
    )

    rendered = engine.render("blog_template.md", report_data)
    blocks = compose_monthly_blog_content(rendered, _render_fragment(engine))

    assert "<h1>全体はプラスです。</h1>" not in blocks
    assert "<div>任天堂はプラスです。</div>" not in blocks
    assert "# 全体はプラスです。" in blocks
    assert "&lt;div&gt;任天堂はプラスです。&lt;/div&gt;" in blocks
    assert "pokebros-monthly-section" not in blocks


def test_wp_publisher_uses_interleaved_monthly_sections(monkeypatch) -> None:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    engine = MarkdownTemplateEngine(str(template_dir))
    markdown_content = engine.render("blog_template.md", _blog_report_data())
    fragment = _render_fragment(engine)
    posted: dict = {}

    class FakeResponse:
        ok = True

        @staticmethod
        def json() -> dict[str, str]:
            return {"link": "https://www.pokebros.net/draft/"}

    def fake_post(*_args, **kwargs):
        posted.update(kwargs["json"])
        return FakeResponse()

    monkeypatch.setattr("collectors.wp_publisher.requests.post", fake_post)
    publisher = WpPublisher("https://www.pokebros.net", "user", "password")

    publisher.create_draft(
        title="月次ブログ",
        markdown_content=markdown_content,
        raw_html_prepend=fragment,
    )

    content = str(posted["content"])
    assert content.count("<!-- wp:html -->") == 4
    assert content.index('id="pf-stock-1"') < content.index("任天堂の振り返り")
    assert content.index("任天堂の振り返り") < content.index('id="pf-stock-2"')
    assert content.rstrip().endswith("<!-- /wp:html -->")

    posted.clear()
    publisher.create_draft(
        title="埋め込みなしの月次ブログ",
        markdown_content=markdown_content,
    )
    native_only_content = str(posted["content"])
    assert "pokebros-monthly-section" not in native_only_content
    assert "今月の全体コメントです。" in native_only_content
    assert "任天堂の個別コメントです。" in native_only_content
