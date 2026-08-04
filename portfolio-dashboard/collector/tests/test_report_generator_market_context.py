"""collectors.report_generator の市況コンテキスト関連のユニットテスト。

_month_change_from_cumulative は DB 非依存の純粋関数なのでそのままテストする。
_get_market_context は DbWriter に依存するため、必要なメソッドだけを持つ
フェイクを使ってテストする（実 DB 接続なし）。
"""

from __future__ import annotations

from collectors.report_generator import (
    BlogReportGenerator,
    _month_change_from_cumulative,
)

# ────────────────────────────────────────────────────────────
# _month_change_from_cumulative（純粋関数）
# ────────────────────────────────────────────────────────────


def test_month_change_from_cumulative_basic() -> None:
    # 前月までの累積 +10%、今月までの累積 +21% → 今月単月は約 +10%
    result = _month_change_from_cumulative(21.0, 10.0)
    assert result == 10.0


def test_month_change_from_cumulative_negative_to_positive() -> None:
    # 前月 -5%、今月 +2% の累積
    result = _month_change_from_cumulative(2.0, -5.0)
    # (1.02 / 0.95 - 1) * 100 ≈ 7.37
    assert result is not None
    assert round(result, 2) == 7.37


def test_month_change_from_cumulative_none_this() -> None:
    assert _month_change_from_cumulative(None, 10.0) is None


def test_month_change_from_cumulative_none_prev() -> None:
    assert _month_change_from_cumulative(5.0, None) is None


def test_month_change_from_cumulative_both_none() -> None:
    assert _month_change_from_cumulative(None, None) is None


def test_month_change_from_cumulative_zero_denominator() -> None:
    # 前月の累積が -100%（分母ゼロ）は理論上あり得ないが、防御的に None を返す
    assert _month_change_from_cumulative(10.0, -100.0) is None


# ────────────────────────────────────────────────────────────
# _get_market_context（フェイク DbWriter でのテスト）
# ────────────────────────────────────────────────────────────


class _FakeDbWriter:
    """DbWriter のうち _get_market_context が使うメソッドだけを持つフェイク。"""

    def __init__(
        self,
        benchmark_rows: dict[str, dict] | None = None,
        exchange_rates: dict[tuple[int, int], float] | None = None,
        raise_on_benchmark: bool = False,
    ) -> None:
        self._benchmark_rows = benchmark_rows or {}
        self._exchange_rates = exchange_rates or {}
        self._raise_on_benchmark = raise_on_benchmark

    def get_benchmark_row(self, date: str) -> dict | None:
        if self._raise_on_benchmark:
            raise RuntimeError("db error")
        return self._benchmark_rows.get(date)

    def get_exchange_rate_for_exact_month(
        self, pair: str, year: int, month: int
    ) -> float | None:
        return self._exchange_rates.get((year, month))


def _make_generator(fake_db: _FakeDbWriter) -> BlogReportGenerator:
    return BlogReportGenerator(fake_db)  # ty: ignore[invalid-argument-type]


def test_get_market_context_full_data() -> None:
    fake_db = _FakeDbWriter(
        benchmark_rows={
            "2026-03-末": {"nikkei225": 21.0, "sp500": 15.0},
            "2026-02-末": {"nikkei225": 10.0, "sp500": 10.0},
        },
        exchange_rates={(2026, 3): 152.34, (2026, 2): 151.0},
    )
    generator = _make_generator(fake_db)
    context = generator._get_market_context(2026, 3)

    assert context["nikkei_change"] == 10.0
    assert context["usdjpy_rate"] == 152.34
    assert context["usdjpy_change"] is not None


def test_get_market_context_missing_prev_month_returns_none() -> None:
    """前月データが無ければ落とさず該当キーを None にする。"""
    fake_db = _FakeDbWriter(
        benchmark_rows={"2026-03-末": {"nikkei225": 21.0, "sp500": 15.0}},
        exchange_rates={(2026, 3): 152.34},
    )
    generator = _make_generator(fake_db)
    context = generator._get_market_context(2026, 3)

    assert context["nikkei_change"] is None
    assert context["sp500_change"] is None
    assert context["usdjpy_rate"] == 152.34
    assert context["usdjpy_change"] is None


def test_get_market_context_all_missing_returns_all_none() -> None:
    fake_db = _FakeDbWriter()
    generator = _make_generator(fake_db)
    context = generator._get_market_context(2026, 3)

    assert context == {
        "nikkei_change": None,
        "sp500_change": None,
        "usdjpy_rate": None,
        "usdjpy_change": None,
    }


def test_get_market_context_does_not_raise_on_db_error() -> None:
    """DB アクセスが例外を投げても市況コンテキスト取得は落とさず全 None を返す。"""
    fake_db = _FakeDbWriter(raise_on_benchmark=True)
    generator = _make_generator(fake_db)
    context = generator._get_market_context(2026, 3)

    assert context == {
        "nikkei_change": None,
        "sp500_change": None,
        "usdjpy_rate": None,
        "usdjpy_change": None,
    }


def test_get_market_context_handles_january_prev_month_year_rollover() -> None:
    """1月の前月は前年12月として参照する。"""
    fake_db = _FakeDbWriter(
        benchmark_rows={
            "2026-01-末": {"nikkei225": 5.0, "sp500": 5.0},
            "2025-12-末": {"nikkei225": 2.0, "sp500": 2.0},
        },
        exchange_rates={(2026, 1): 150.0, (2025, 12): 149.0},
    )
    generator = _make_generator(fake_db)
    context = generator._get_market_context(2026, 1)

    assert context["nikkei_change"] is not None
    assert context["usdjpy_change"] is not None
