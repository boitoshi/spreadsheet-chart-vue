"""app/sheets/utils.py のユニットテスト"""

import pytest
from app.sheets.utils import to_float, to_float_or_none


class TestToFloat:
    def test_整数文字列を変換できる(self):
        assert to_float("1234") == 1234.0

    def test_小数文字列を変換できる(self):
        assert to_float("12.34") == 12.34

    def test_カンマ区切りの数値文字列を変換できる(self):
        assert to_float("1,234,567") == 1234567.0

    def test_数値をそのまま返す(self):
        assert to_float(42.5) == 42.5

    def test_ゼロを返す(self):
        assert to_float(0) == 0.0

    def test_変換できない文字列は0を返す(self):
        assert to_float("abc") == 0.0

    def test_Noneは0を返す(self):
        assert to_float(None) == 0.0

    def test_空文字列は0を返す(self):
        assert to_float("") == 0.0

    def test_マイナス値を変換できる(self):
        assert to_float("-500") == -500.0


class TestToFloatOrNone:
    def test_数値文字列を変換できる(self):
        assert to_float_or_none("123.45") == pytest.approx(123.45)

    def test_カンマ区切りの数値を変換できる(self):
        assert to_float_or_none("1,000") == 1000.0

    def test_Noneを受け取るとNoneを返す(self):
        assert to_float_or_none(None) is None

    def test_空文字列はNoneを返す(self):
        assert to_float_or_none("") is None

    def test_変換できない文字列はNoneを返す(self):
        assert to_float_or_none("N/A") is None

    def test_ゼロ文字列は0_0を返す(self):
        assert to_float_or_none("0") == 0.0

    def test_マイナス値を変換できる(self):
        assert to_float_or_none("-1.5") == pytest.approx(-1.5)
