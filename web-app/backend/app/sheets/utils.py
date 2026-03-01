"""sheets モジュール共通ヘルパー関数"""

from datetime import date


def to_float(value) -> float:
    """文字列・数値をfloatに変換する。失敗時は0.0を返す"""
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def to_float_or_none(value) -> float | None:
    """文字列・数値をfloatに変換する。空値の場合はNoneを返す"""
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def calc_cagr(
    total_cost: float,
    current_value: float,
    acquired_date: str,
) -> float | None:
    """CAGR計算。保有期間1年未満・データ不足はNoneを返す"""
    if not acquired_date or total_cost <= 0 or current_value <= 0:
        return None
    try:
        acq = date.fromisoformat(acquired_date)
    except ValueError:
        return None
    years = (date.today() - acq).days / 365.25
    if years < 1:
        return None
    return (current_value / total_cost) ** (1 / years) - 1
