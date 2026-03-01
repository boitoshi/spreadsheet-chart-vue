"""sheets モジュール共通ヘルパー関数"""


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
