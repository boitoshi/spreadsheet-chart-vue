"""collectors.ai_comment のプロンプト整形関数のユニットテスト。

Anthropic API 自体は呼び出さず、プロンプト・システムプロンプトの整形ロジック
（market_context の整形、None 時の省略、ハルシネーション禁止指示の存在）のみを
検証する。
"""

from __future__ import annotations

from collectors.ai_comment import (
    _BEGINNER_GUARD,
    _HALLUCINATION_GUARD,
    _build_intro_prompt,
    _build_stock_prompt,
    _build_summary_prompt,
    _format_market_context,
)

# ────────────────────────────────────────────────────────────
# フィクスチャ
# ────────────────────────────────────────────────────────────

FULL_MARKET_CONTEXT = {
    "nikkei_change": 3.25,
    "sp500_change": -1.10,
    "usdjpy_rate": 152.34,
    "usdjpy_change": 0.85,
}

STOCK_DATA = {
    "name": "任天堂",
    "symbol": "7974.T",
    "current_price": 8500,
    "pl": 12000,
    "pl_rate": 5.5,
    "currency": "JPY",
    "market_data": {"change_rate": 2.1},
}

PORTFOLIO_DATA = {
    "total_value": 500000,
    "total_pl": 25000,
    "total_pl_rate": 5.26,
    "holdings": [STOCK_DATA],
}


# ────────────────────────────────────────────────────────────
# _format_market_context
# ────────────────────────────────────────────────────────────


def test_format_market_context_with_full_data() -> None:
    text = _format_market_context(FULL_MARKET_CONTEXT)
    assert "日経平均株価" in text
    assert "+3.25%" in text
    assert "S&P500" in text
    assert "-1.10%" in text
    assert "USD/JPY" in text
    assert "152.34円" in text
    assert "+0.85%" in text


def test_format_market_context_omits_none_fields() -> None:
    partial = {
        "nikkei_change": 3.25,
        "sp500_change": None,
        "usdjpy_rate": None,
        "usdjpy_change": None,
    }
    text = _format_market_context(partial)
    assert "日経平均株価" in text
    assert "S&P500" not in text
    assert "USD/JPY" not in text


def test_format_market_context_usdjpy_rate_without_change() -> None:
    """usdjpy_rate はあるが usdjpy_change が無い（前月データなし）場合、
    レートだけ記載し前月比は書かない。"""
    partial = {
        "nikkei_change": None,
        "sp500_change": None,
        "usdjpy_rate": 152.34,
        "usdjpy_change": None,
    }
    text = _format_market_context(partial)
    assert "152.34円" in text
    assert "前月比" not in text


def test_format_market_context_all_none_returns_no_data_notice() -> None:
    empty = {
        "nikkei_change": None,
        "sp500_change": None,
        "usdjpy_rate": None,
        "usdjpy_change": None,
    }
    text = _format_market_context(empty)
    assert "市況データなし" in text
    assert "言及はしないこと" in text


def test_format_market_context_handles_none_input() -> None:
    """market_context 自体が None（report_data に無い場合）でも例外を出さない。"""
    text = _format_market_context(None)
    assert "市況データなし" in text


def test_format_market_context_handles_empty_dict() -> None:
    text = _format_market_context({})
    assert "市況データなし" in text


# ────────────────────────────────────────────────────────────
# 禁止指示（ハルシネーション対策）の存在確認
# ────────────────────────────────────────────────────────────


def test_hallucination_guard_forbids_unlisted_events() -> None:
    """ニュース・イベント等、与えられていない出来事への言及を禁止する文言があること。"""
    assert "ニュース" in _HALLUCINATION_GUARD
    assert "禁止" in _HALLUCINATION_GUARD
    assert "推測" in _HALLUCINATION_GUARD


def test_beginner_guard_requires_term_explanation() -> None:
    assert "専門用語" in _BEGINNER_GUARD


def test_stock_prompt_instructs_no_speculation_on_cause() -> None:
    prompt = _build_stock_prompt(STOCK_DATA, 2026, 3, FULL_MARKET_CONTEXT)
    assert "断定したり推測したりしないこと" in prompt
    # 記載のない指標には言及しないよう明示していること
    assert "記載のない指標には言及しないこと" in prompt


def test_summary_prompt_instructs_no_unlisted_reference() -> None:
    prompt = _build_summary_prompt(PORTFOLIO_DATA, 2026, 3, FULL_MARKET_CONTEXT)
    assert "記載のない指標には言及しないこと" in prompt


def test_intro_prompt_instructs_no_unlisted_reference() -> None:
    prompt = _build_intro_prompt(PORTFOLIO_DATA, 2026, 3, FULL_MARKET_CONTEXT)
    assert "記載のない指標には言及しないこと" in prompt


# ────────────────────────────────────────────────────────────
# プロンプトへの実データ埋め込み確認
# ────────────────────────────────────────────────────────────


def test_stock_prompt_embeds_facts_and_market_context() -> None:
    prompt = _build_stock_prompt(STOCK_DATA, 2026, 3, FULL_MARKET_CONTEXT)
    assert "任天堂" in prompt
    assert "7974.T" in prompt
    assert "2026年3月" in prompt
    assert "日経平均株価" in prompt


def test_stock_prompt_works_without_market_context() -> None:
    """market_context が None でも例外にならず、市況データなしの旨が入る。"""
    prompt = _build_stock_prompt(STOCK_DATA, 2026, 3, None)
    assert "市況データなし" in prompt


def test_summary_prompt_lists_holdings() -> None:
    prompt = _build_summary_prompt(PORTFOLIO_DATA, 2026, 3, FULL_MARKET_CONTEXT)
    assert "任天堂（7974.T）" in prompt
    assert "+5.50%" in prompt


def test_summary_prompt_handles_no_holdings() -> None:
    empty_portfolio = {
        "total_value": 0,
        "total_pl": 0,
        "total_pl_rate": 0,
        "holdings": [],
    }
    prompt = _build_summary_prompt(empty_portfolio, 2026, 3, None)
    assert "保有銘柄なし" in prompt
