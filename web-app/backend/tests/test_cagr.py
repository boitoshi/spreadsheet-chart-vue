"""calc_cagr のユニットテスト"""
from datetime import date, timedelta

from app.sheets.utils import calc_cagr


def _date_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


class TestCalcCagr:
    def test_normal_gain(self):
        """2年保有・利益ありで正の CAGR が返る"""
        acquired = _date_ago(730)
        result = calc_cagr(100_000, 120_000, acquired)
        assert result is not None
        assert result > 0
        # 2年で20%増 → CAGR ≈ 0.0954
        assert abs(result - ((1.2) ** 0.5 - 1)) < 0.01

    def test_less_than_one_year(self):
        """1年未満保有は None"""
        acquired = _date_ago(300)
        assert calc_cagr(100_000, 120_000, acquired) is None

    def test_empty_acquired_date(self):
        """acquiredDate が空文字は None"""
        assert calc_cagr(100_000, 120_000, "") is None

    def test_zero_total_cost(self):
        """total_cost = 0 は None"""
        acquired = _date_ago(730)
        assert calc_cagr(0, 120_000, acquired) is None

    def test_negative_return(self):
        """損失ケース（CAGR がマイナス）"""
        acquired = _date_ago(730)
        result = calc_cagr(100_000, 80_000, acquired)
        assert result is not None
        assert result < 0

    def test_invalid_date_format(self):
        """不正な日付形式は None"""
        assert calc_cagr(100_000, 120_000, "invalid-date") is None

    def test_exactly_one_year(self):
        """ちょうど1年保有は有効な CAGR を返す"""
        acquired = _date_ago(366)
        result = calc_cagr(100_000, 120_000, acquired)
        assert result is not None

    def test_zero_current_value(self):
        """current_value = 0 は None"""
        acquired = _date_ago(730)
        assert calc_cagr(100_000, 0, acquired) is None
