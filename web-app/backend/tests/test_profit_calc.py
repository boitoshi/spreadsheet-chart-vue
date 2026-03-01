"""
損益分離計算ロジックのユニットテスト。

fetch_performance() はGoogle Sheetsへの接続を持つため、
計算ロジック部分のみをインライン関数として抽出してテストする。
"""

import pytest


def _calc_profit(
    profit: float,
    shares: float,
    currency: str,
    acquired_price_foreign: float | None,
    current_price_foreign: float | None,
    acquired_exchange_rate: float | None,
    current_exchange_rate: float | None,
) -> tuple[float, float]:
    """
    performance.py の損益分離計算と同一ロジック。
    Returns: (stock_profit, fx_profit)
    """
    if (
        currency == "JPY"
        or acquired_price_foreign is None
        or current_price_foreign is None
        or acquired_exchange_rate is None
        or current_exchange_rate is None
    ):
        return profit, 0.0
    price_diff = current_price_foreign - acquired_price_foreign
    stock_profit = price_diff * acquired_exchange_rate * shares
    rate_diff = current_exchange_rate - acquired_exchange_rate
    fx_profit = rate_diff * current_price_foreign * shares
    return stock_profit, fx_profit


class TestJpyStockProfitCalc:
    """JPY建て銘柄は損益がそのまま株価損益、為替損益はゼロ"""

    def test_JPY銘柄の株価損益は損益と等しい(self):
        stock, fx = _calc_profit(
            profit=50000,
            shares=100,
            currency="JPY",
            acquired_price_foreign=None,
            current_price_foreign=None,
            acquired_exchange_rate=None,
            current_exchange_rate=None,
        )
        assert stock == 50000
        assert fx == 0.0

    def test_JPY銘柄の損失ケース(self):
        stock, fx = _calc_profit(
            profit=-30000,
            shares=200,
            currency="JPY",
            acquired_price_foreign=None,
            current_price_foreign=None,
            acquired_exchange_rate=None,
            current_exchange_rate=None,
        )
        assert stock == -30000
        assert fx == 0.0


class TestForeignStockProfitCalc:
    """外貨建て銘柄の株価損益・為替損益分離計算"""

    def test_株価上昇のみ為替変動なし(self):
        # NVDA: 取得 $500, 月末 $600, 為替 150円 固定, 10株
        stock, fx = _calc_profit(
            profit=150000,  # (600-500)*150*10
            shares=10,
            currency="USD",
            acquired_price_foreign=500.0,
            current_price_foreign=600.0,
            acquired_exchange_rate=150.0,
            current_exchange_rate=150.0,
        )
        assert stock == pytest.approx(150000.0)  # (600-500)*150*10
        assert fx == pytest.approx(0.0)          # (150-150)*600*10

    def test_為替上昇のみ株価変動なし(self):
        # NVDA: 株価 $500 固定, 為替 150→155円, 10株
        stock, fx = _calc_profit(
            profit=25000,  # (155-150)*500*10
            shares=10,
            currency="USD",
            acquired_price_foreign=500.0,
            current_price_foreign=500.0,
            acquired_exchange_rate=150.0,
            current_exchange_rate=155.0,
        )
        assert stock == pytest.approx(0.0)       # (500-500)*150*10
        assert fx == pytest.approx(25000.0)      # (155-150)*500*10

    def test_株価損益と為替損益の合計が総損益と一致する(self):
        # NVDA: 取得 $500/150円, 月末 $600/155円, 10株
        # 株価損益 = (600-500)*150*10 = 150,000
        # 為替損益 = (155-150)*600*10 = 30,000
        # 総損益   = 150,000 + 30,000 = 180,000
        profit = 180000.0
        stock, fx = _calc_profit(
            profit=profit,
            shares=10,
            currency="USD",
            acquired_price_foreign=500.0,
            current_price_foreign=600.0,
            acquired_exchange_rate=150.0,
            current_exchange_rate=155.0,
        )
        assert stock == pytest.approx(150000.0)
        assert fx == pytest.approx(30000.0)
        assert stock + fx == pytest.approx(profit)

    def test_株価下落かつ為替上昇(self):
        # 株価損益 = (450-500)*150*10 = -75,000
        # 為替損益 = (155-150)*450*10 = 22,500
        stock, fx = _calc_profit(
            profit=-52500.0,
            shares=10,
            currency="USD",
            acquired_price_foreign=500.0,
            current_price_foreign=450.0,
            acquired_exchange_rate=150.0,
            current_exchange_rate=155.0,
        )
        assert stock == pytest.approx(-75000.0)
        assert fx == pytest.approx(22500.0)
        assert stock + fx == pytest.approx(-52500.0)


class TestForeignDataMissing:
    """外貨データが欠損している場合はJPY扱いにフォールバックする"""

    def test_外貨単価が欠損の場合はフォールバック(self):
        stock, fx = _calc_profit(
            profit=10000,
            shares=10,
            currency="USD",
            acquired_price_foreign=None,
            current_price_foreign=600.0,
            acquired_exchange_rate=150.0,
            current_exchange_rate=155.0,
        )
        assert stock == 10000
        assert fx == 0.0

    def test_為替レートが欠損の場合はフォールバック(self):
        stock, fx = _calc_profit(
            profit=10000,
            shares=10,
            currency="USD",
            acquired_price_foreign=500.0,
            current_price_foreign=600.0,
            acquired_exchange_rate=None,
            current_exchange_rate=155.0,
        )
        assert stock == 10000
        assert fx == 0.0
