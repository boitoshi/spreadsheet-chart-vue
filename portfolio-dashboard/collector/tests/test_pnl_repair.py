"""collectors.pnl_repair のユニットテスト。

compute_row_update は DB 非依存の純粋関数なので、フィクスチャの dict のみで
テストする。フィクスチャは実データ（NVDA・任天堂）ベースの移行ミス行を使う。
"""

from __future__ import annotations

import copy

import pytest

from collectors.pnl_repair import compute_row_update

# ────────────────────────────────────────────────────────────
# フィクスチャ（実データベース）
# ────────────────────────────────────────────────────────────

# NVDA 買付履歴 3 件（price は外国株なので 0.0 固定）
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

# 2024-12-末 NVDA: 移行ミスにより「最後の買付行のみ」の株数（shares=1）になっている行
NVDA_2024_12_MIGRATION_MISTAKE_ROW = {
    "date": "2024-12-末",
    "code": "NVDA",
    "name": "エヌビディア",
    "acquired_price": 20369.08,
    "current_price": 21048.77,
    "shares": 1.0,
    "cost": 20369.08,
    "value": 21048.77,
    "profit": 679.69,
    "profit_rate": 3.34,
    "currency": "USD",
    "acquired_price_foreign": 129.88,
    "current_price_foreign": 130.68,
    "acquired_exchange_rate": 156.83,
    "current_exchange_rate": 161.06,
}

# 任天堂 買付履歴 1 件（初回購入のみ）
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
]

# 2023-06-末 任天堂: 移行済みで既に正しい行（1 株のみ保有）
NINTENDO_2023_06_ALREADY_CORRECT_ROW = {
    "date": "2023-06-末",
    "code": "7974.T",
    "name": "任天堂",
    "acquired_price": 6433,
    "current_price": 6433,
    "shares": 1,
    "cost": 6433,
    "value": 6433,
    "profit": 0,
    "profit_rate": 0.0,
    "currency": "JPY",
    "acquired_price_foreign": 6433,
    "current_price_foreign": 6433,
    "acquired_exchange_rate": 1.0,
    "current_exchange_rate": 1.0,
}


@pytest.fixture
def nvda_purchases() -> list[dict]:
    return copy.deepcopy(NVDA_PURCHASES)


@pytest.fixture
def nvda_migration_mistake_row() -> dict:
    return copy.deepcopy(NVDA_2024_12_MIGRATION_MISTAKE_ROW)


@pytest.fixture
def nintendo_purchases() -> list[dict]:
    return copy.deepcopy(NINTENDO_PURCHASES)


@pytest.fixture
def nintendo_already_correct_row() -> dict:
    return copy.deepcopy(NINTENDO_2023_06_ALREADY_CORRECT_ROW)


# ────────────────────────────────────────────────────────────
# テストケース
# ────────────────────────────────────────────────────────────


def test_移行ミス行を正しい累積値に補正する(nvda_migration_mistake_row, nvda_purchases):
    """2024-12-末 NVDA: shares=1（誤）→ shares=4（seq1+seq2 の累積）に補正される。

    seq3（2025-12-15 購入）は対象月より後なので累積に含まれない。
    """
    result = compute_row_update(nvda_migration_mistake_row, nvda_purchases)
    assert result is not None
    update, changes = result

    # cost = 3株×132.11×161.77（seq1） + 1株×129.88×156.83（seq2） の円建てコスト
    expected_cost = 3 * 132.11 * 161.77 + 129.88 * 156.83
    # value = current_price（変更しない既存値） × 補正後 shares
    expected_value = 4 * 21048.77
    # avg_price_foreign（ネイティブ通貨建て平均取得単価）
    expected_avg_native = (3 * 132.11 + 129.88) / 4
    # profit は丸め後 value - cost（compute_row_update と同じ丸め規約で算出）
    expected_profit = round(expected_value, 2) - round(expected_cost, 2)

    assert update["shares"] == pytest.approx(4.0)
    assert update["cost"] == pytest.approx(84483.38, abs=0.01)
    assert update["cost"] == pytest.approx(expected_cost, abs=0.01)
    assert update["value"] == pytest.approx(84195.08, abs=0.01)
    assert update["value"] == pytest.approx(expected_value, abs=0.01)
    assert update["acquired_price_foreign"] == pytest.approx(131.55, abs=0.01)
    assert update["acquired_price_foreign"] == pytest.approx(
        expected_avg_native, abs=0.01
    )
    assert update["profit"] == pytest.approx(expected_profit, abs=0.01)

    # shares 以外にも取得系フィールドが変更対象になっている
    changed_fields = {field for field, _, _ in changes}
    assert "shares" in changed_fields
    assert "cost" in changed_fields


def test_買付前の月はNoneを返す(nvda_purchases):
    """2024-06-末（NVDA 初回購入 2024-07-10 より前）は累積株数 0 のため None。"""
    row = {
        "date": "2024-06-末",
        "code": "NVDA",
        "current_price": 20000.0,
        "shares": 0,
        "cost": 0,
        "acquired_price": 0,
        "acquired_price_foreign": 0,
        "acquired_exchange_rate": 0,
        "value": 0,
        "profit": 0,
        "profit_rate": 0,
        "currency": "USD",
    }

    result = compute_row_update(row, nvda_purchases)
    assert result is None


def test_冪等性_補正後の値を再度計算すると変更なし(
    nvda_migration_mistake_row, nvda_purchases
):
    """補正後の値を反映した行に対して再度 compute_row_update しても差分が出ない。"""
    result = compute_row_update(nvda_migration_mistake_row, nvda_purchases)
    assert result is not None
    update, _changes = result

    repaired_row = {**nvda_migration_mistake_row, **update}
    result_again = compute_row_update(repaired_row, nvda_purchases)
    assert result_again is not None
    _update_again, changes_again = result_again

    assert changes_again == []


def test_UPDATE辞書に現在価格系のキーを含めない(
    nvda_migration_mistake_row, nvda_purchases
):
    """current_price / current_price_foreign / current_exchange_rate / currency /
    name は保存済みの正しい市場データなので UPDATE 対象に含めてはならない。"""
    result = compute_row_update(nvda_migration_mistake_row, nvda_purchases)
    assert result is not None
    update, _changes = result

    forbidden_keys = {
        "current_price",
        "current_price_foreign",
        "current_exchange_rate",
        "currency",
        "name",
    }
    assert forbidden_keys.isdisjoint(update.keys())


def test_日本株の既に正しい行は変更なし(
    nintendo_already_correct_row, nintendo_purchases
):
    """既に正しい任天堂の行は補正しても変更リストが空になる。"""
    result = compute_row_update(nintendo_already_correct_row, nintendo_purchases)
    assert result is not None
    _update, changes = result

    assert changes == []
