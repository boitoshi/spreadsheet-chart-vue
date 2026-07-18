"""collectors.purchase_math.time_weighted_returns のユニットテスト。

時間加重リターン（TWR）計算が、追加買付フローの投入額をリターンとして
誤計上しないことを検証する。
"""

from __future__ import annotations

import pytest

from collectors.purchase_math import time_weighted_returns


def test_basic_chain() -> None:
    """基本連鎖: 2 か月分の月次リターンが正しく複利連鎖する。

    月1: cost=100, value=110 → F_0=100, D_0=100, r_0=110/100-1=10.0% → 累積10.0%
    月2: cost=200, value=220 → F_1=cost差分=100, D_1=前月value(110)+F_1(100)=210
         r_1=220/210-1≈4.7619% → 累積 = 1.10 × 1.047619 - 1 ≈ 15.2381% → 15.24%
    """
    series = [("2025-01", 110.0, 100.0), ("2025-02", 220.0, 200.0)]
    result = time_weighted_returns(series)

    assert result["2025-01"] == pytest.approx(10.0)
    assert result["2025-02"] == pytest.approx(15.24, abs=0.01)


def test_flow_only_month_does_not_move_cumulative() -> None:
    """回帰テスト: 買い増しただけで株価が変わらない月は累積リターンが動かない。

    月1: cost=100, value=100 → r_0=100/100-1=0% → 累積0%
    月2: cost=200, value=200（買い増しのみ・株価不変）
         F_1=100, D_1=前月value(100)+F_1(100)=200, r_1=200/200-1=0%
         → 累積0%

    旧式（(value-first_cost)/first_cost）だと (200-100)/100=+100% になって
    しまうバグを回帰させないためのテスト。
    """
    series = [("2025-01", 100.0, 100.0), ("2025-02", 200.0, 200.0)]
    result = time_weighted_returns(series)

    assert result["2025-01"] == pytest.approx(0.0)
    assert result["2025-02"] == pytest.approx(0.0)


def test_missing_month_is_bridged() -> None:
    """欠損月またぎ: 月2 が存在しなくても月1→月3 でそのまま連鎖する。

    月1: cost=100, value=110 → r_0=110/100-1=10.0% → 累積10.0%
    月3: cost=200, value=231（月2 は series に存在しない）
         F=cost差分=100, D=前月value(110)+F(100)=210
         r=231/210-1=10.0% → 累積 = 1.10 × 1.10 - 1 = 21.0%
    """
    series = [("2025-01", 110.0, 100.0), ("2025-03", 231.0, 200.0)]
    result = time_weighted_returns(series)

    assert result["2025-01"] == pytest.approx(10.0)
    assert result["2025-03"] == pytest.approx(21.0)


def test_zero_denominator_guard() -> None:
    """D=0 防御: 分母が0以下でもゼロ除算せず0.0%を返す。"""
    series = [("2025-01", 0.0, 0.0)]
    result = time_weighted_returns(series)

    assert result["2025-01"] == pytest.approx(0.0)


def test_negative_rate() -> None:
    """下落: cost=100, value=90 → r=90/100-1=-10.0%"""
    series = [("2025-01", 90.0, 100.0)]
    result = time_weighted_returns(series)

    assert result["2025-01"] == pytest.approx(-10.0)


def test_rounded_to_two_decimals() -> None:
    """結果が小数2桁に丸められていること。"""
    series = [("2025-01", 110.0, 100.0), ("2025-02", 220.0, 200.0)]
    result = time_weighted_returns(series)

    for value in result.values():
        assert value == round(value, 2)


def test_empty_series() -> None:
    """空リストを渡すと空辞書を返す。"""
    assert time_weighted_returns([]) == {}
