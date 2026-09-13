"""ブログ用埋め込みと編集可能コメントの分離テスト。"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import markdown

from collectors import embed_generator as embed_generator_module
from collectors.block_converter import GutenbergBlockConverter
from collectors.db_writer import DbWriter
from collectors.embed_generator import EmbedGenerator
from collectors.template_engine import MarkdownTemplateEngine


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
            }
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


def test_blog_template_makes_comments_editable_and_keeps_fixed_promo() -> None:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    engine = MarkdownTemplateEngine(str(template_dir))

    rendered = engine.render("blog_template.md", _blog_report_data())
    html = markdown.markdown(rendered)
    blocks = GutenbergBlockConverter().convert(html)

    assert "## 今月の振り返り" in rendered
    assert "### 任天堂" in rendered
    assert "### DeNA" in rendered
    assert "今月の全体コメントです。" in blocks
    assert "任天堂の個別コメントです。" in blocks
    assert "DeNAの個別コメントです。" in blocks
    assert blocks.count("<!-- wp:paragraph -->") >= 3
    assert "<!-- wp:html -->" not in blocks

    assert "https://portfolio.pokebros.net/reports/2026/8" in rendered
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
    html = markdown.markdown(rendered)
    blocks = GutenbergBlockConverter().convert(html)

    assert "<h1>全体はプラスです。</h1>" not in html
    assert "<div>任天堂はプラスです。</div>" not in html
    assert "# 全体はプラスです。" in blocks
    assert "&lt;div&gt;任天堂はプラスです。&lt;/div&gt;" in blocks
    assert "<!-- wp:html -->" not in blocks
