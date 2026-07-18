"""collectors.purchase_math のユニットテスト。

フィクスチャは実データ（任天堂 7974.T・NVDA）をそのまま dict リスト化して使用する。
"""

from __future__ import annotations

import copy
import random

import pytest

from collectors.purchase_math import cumulative_position, sort_purchases

# ────────────────────────────────────────────────────────────
# フィクスチャ（実データ）
# ────────────────────────────────────────────────────────────

# 任天堂 7974.T（日本株）: price に円単価、price_foreign / exchange_rate は None
NINTENDO_PURCHASES = [
    {
        "code": "7974.T",
        "seq": 1,
        "shares": 1,
        "price": 6433,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2023-06-28",
    },
    {
        "code": "7974.T",
        "seq": 2,
        "shares": 1,
        "price": 8875,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2024-07-03",
    },
    {
        "code": "7974.T",
        "seq": 3,
        "shares": 1,
        "price": 9150,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2025-01-22",
    },
    {
        "code": "7974.T",
        "seq": 4,
        "shares": 1,
        "price": 13105,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2025-07-07",
    },
    {
        "code": "7974.T",
        "seq": 5,
        "shares": 1,
        "price": 11731,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2025-12-12",
    },
    {
        "code": "7974.T",
        "seq": 6,
        "shares": 1,
        "price": 10499,
        "price_foreign": None,
        "exchange_rate": None,
        "purchased_at": "2025-12-22",
    },
]

# NVDA（外国株）: price は 0.0、price_foreign に外貨単価、exchange_rate に買付時為替
NVDA_PURCHASES = [
    {
        "code": "NVDA",
        "seq": 1,
        "shares": 3,
        "price": 0.0,
        "price_foreign": 132.11,
        "exchange_rate": 161.77,
        "purchased_at": "2024-07-10",
    },
    {
        "code": "NVDA",
        "seq": 2,
        "shares": 1,
        "price": 0.0,
        "price_foreign": 129.88,
        "exchange_rate": 156.83,
        "purchased_at": "2024-12-23",
    },
    {
        "code": "NVDA",
        "seq": 3,
        "shares": 1,
        "price": 0.0,
        "price_foreign": 181.08,
        "exchange_rate": 156.16,
        "purchased_at": "2025-12-15",
    },
]


@pytest.fixture
def nintendo_purchases() -> list[dict]:
    """任天堂の買付履歴（テストごとに独立したコピーを返す）。"""
    return copy.deepcopy(NINTENDO_PURCHASES)


@pytest.fixture
def nvda_purchases() -> list[dict]:
    """NVDA の買付履歴（テストごとに独立したコピーを返す）。"""
    return copy.deepcopy(NVDA_PURCHASES)


# ────────────────────────────────────────────────────────────
# テストケース
# ────────────────────────────────────────────────────────────


def test_nintendo_2025_12_全件累積(nintendo_purchases):
    """任天堂 (2025, 12): 6 件全てが累積される。"""
    pos = cumulative_position(nintendo_purchases, 2025, 12, is_foreign=False)

    assert pos.shares == pytest.approx(6)
    assert pos.cost_jpy == pytest.approx(59793.0)
    assert pos.avg_price_jpy == pytest.approx(9965.50)


def test_nintendo_2025_11_12月分は含まない(nintendo_purchases):
    """任天堂 (2025, 11): 12 月の 2 件（seq5, seq6）は含まれない。"""
    pos = cumulative_position(nintendo_purchases, 2025, 11, is_foreign=False)

    assert pos.shares == pytest.approx(4)
    assert pos.cost_jpy == pytest.approx(37563)
    assert pos.avg_price_jpy == pytest.approx(9390.75)


def test_nintendo_初回購入月_月中買付が当月末に反映される(nintendo_purchases):
    """任天堂 (2023, 6): 初回購入（月中の買付）が当月末残高に反映される。"""
    pos = cumulative_position(nintendo_purchases, 2023, 6, is_foreign=False)

    assert pos.shares == pytest.approx(1)
    assert pos.avg_price_jpy == pytest.approx(6433)


def test_nvda_2025_12_ネイティブ通貨(nvda_purchases):
    """NVDA (2025, 12): ネイティブ通貨建ての累積ポジション。"""
    pos = cumulative_position(nvda_purchases, 2025, 12, is_foreign=True)

    assert pos.shares == pytest.approx(5)
    assert pos.avg_price_native == pytest.approx(141.458, abs=1e-3)
    assert pos.cost_native == pytest.approx(707.29, abs=1e-2)


def test_nvda_2025_12_円建てとコスト加重為替レート(nvda_purchases):
    """NVDA (2025, 12): 円建てコストとコスト加重平均為替レート。"""
    pos = cumulative_position(nvda_purchases, 2025, 12, is_foreign=True)

    assert pos.cost_jpy == pytest.approx(112760.84, abs=0.01)
    assert pos.avg_exchange_rate == pytest.approx(159.4266, abs=1e-3)


def test_買付前の月は残高ゼロ(nintendo_purchases):
    """任天堂 (2023, 5): 初回購入（2023-06-28）より前は残高ゼロ。"""
    pos = cumulative_position(nintendo_purchases, 2023, 5, is_foreign=False)

    assert pos.shares == pytest.approx(0)
    assert pos.avg_price_jpy == pytest.approx(0.0)
    assert pos.avg_price_native == pytest.approx(0.0)
    assert pos.avg_exchange_rate == pytest.approx(0.0)


def test_月境界_12月12日購入は11月に含まれず12月に含まれる(nintendo_purchases):
    """seq5（2025-12-12 購入）が (2025, 11) では未反映、(2025, 12) で反映される。"""
    pos_nov = cumulative_position(nintendo_purchases, 2025, 11, is_foreign=False)
    pos_dec = cumulative_position(nintendo_purchases, 2025, 12, is_foreign=False)

    assert pos_nov.shares == pytest.approx(4)
    assert pos_dec.shares == pytest.approx(6)


def test_入力順シャッフルでも結果不変(nintendo_purchases):
    """sort_purchases の規約により、入力順（シャッフル）に関わらず結果が一致する。"""
    shuffled = copy.deepcopy(nintendo_purchases)
    random.Random(42).shuffle(shuffled)

    # 並び替え結果自体が purchased_at 昇順 → seq 昇順になっていることを確認
    sorted_original = sort_purchases(nintendo_purchases)
    sorted_shuffled = sort_purchases(shuffled)
    assert sorted_original == sorted_shuffled

    pos_original = cumulative_position(nintendo_purchases, 2025, 12, is_foreign=False)
    pos_shuffled = cumulative_position(shuffled, 2025, 12, is_foreign=False)

    assert pos_shuffled.shares == pytest.approx(pos_original.shares)
    assert pos_shuffled.cost_jpy == pytest.approx(pos_original.cost_jpy)
    assert pos_shuffled.avg_price_jpy == pytest.approx(pos_original.avg_price_jpy)


def test_日本株はavg_exchange_rateが1になる(nintendo_purchases):
    """日本株は cost_jpy == cost_native なので avg_exchange_rate == 1.0。"""
    pos = cumulative_position(nintendo_purchases, 2025, 12, is_foreign=False)

    assert pos.cost_jpy == pytest.approx(pos.cost_native)
    assert pos.avg_exchange_rate == pytest.approx(1.0)


def test_外国株でexchange_rateがNoneならValueError(nvda_purchases):
    """外国株の買付に exchange_rate が None のものがあれば ValueError を送出する。"""
    nvda_purchases[0]["exchange_rate"] = None

    with pytest.raises(ValueError):
        cumulative_position(nvda_purchases, 2025, 12, is_foreign=True)


def test_外国株でexchange_rateが0ならValueError(nvda_purchases):
    """外国株の買付に exchange_rate が 0 のものがあれば ValueError を送出する。"""
    nvda_purchases[0]["exchange_rate"] = 0

    with pytest.raises(ValueError):
        cumulative_position(nvda_purchases, 2025, 12, is_foreign=True)


def test_purchased_at空文字は常に累積対象(nintendo_purchases):
    """purchased_at="" の買付は (0, 0) 扱いとなり、任意の対象月で常に累積される。"""
    purchases = copy.deepcopy(nintendo_purchases)[:1]
    purchases[0]["purchased_at"] = ""
    purchases[0]["price"] = 5000

    # 過去・現在どちらの対象月を指定しても常に累積対象になる
    pos_past = cumulative_position(purchases, 2000, 1, is_foreign=False)
    pos_future = cumulative_position(purchases, 2030, 12, is_foreign=False)

    assert pos_past.shares == pytest.approx(1)
    assert pos_past.avg_price_jpy == pytest.approx(5000)
    assert pos_future.shares == pytest.approx(1)
    assert pos_future.avg_price_jpy == pytest.approx(5000)
