"""Markdownテンプレートエンジンモジュール"""

import json
from decimal import ROUND_HALF_UP, Decimal

from jinja2 import Environment, FileSystemLoader, select_autoescape


class MarkdownTemplateEngine:
    """Markdownテンプレートエンジン"""

    def __init__(self, template_dir: str = "templates") -> None:
        """初期化

        Args:
            template_dir: テンプレートディレクトリのパス
        """
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(enabled_extensions=(), default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # カスタムフィルタを追加
        self.env.filters["format_currency"] = self._format_currency
        self.env.filters["format_number"] = self._format_number
        self.env.filters["format_percent"] = self._format_percent
        self.env.filters["format_price"] = self._format_price
        self.env.filters["format_json"] = self._format_json

    def render(self, template_name: str, data: dict) -> str:
        """テンプレートをレンダリング

        Args:
            template_name: テンプレートファイル名
            data: レンダリングデータ

        Returns:
            レンダリング済みMarkdown文字列
        """
        template = self.env.get_template(template_name)
        return template.render(**data)

    def _format_currency(self, value: float | int | None) -> str:
        """通貨フォーマット（カンマ区切り、四捨五入）

        Args:
            value: 数値

        Returns:
            フォーマット済み文字列
        """
        if value is None:
            return "0"
        # Decimal で正確な四捨五入を行う
        d = Decimal(str(value))
        # 小数第0位（円単位）へ四捨五入
        rounded = d.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        # 3桁カンマ区切り
        return f"{int(rounded):,}"

    def _format_number(self, value: float | int | None, decimals: int = 2) -> str:
        """数値フォーマット（四捨五入）

        Args:
            value: 数値
            decimals: 小数点以下の桁数

        Returns:
            フォーマット済み文字列
        """
        if value is None:
            return "0"
        # Decimal で正確な四捨五入を行う
        d = Decimal(str(value))
        # 指定桁数へ四捨五入
        quantize_str = "1" if decimals == 0 else "0." + "0" * decimals
        rounded = d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        # 3桁カンマ区切り
        return f"{rounded:,}"

    def _format_percent(self, value: float | int | None, decimals: int = 1) -> str:
        """パーセントフォーマット（四捨五入）

        Args:
            value: 数値（%の数値そのもの）
            decimals: 小数点以下の桁数

        Returns:
            フォーマット済み文字列（+記号付き）
        """
        if value is None:
            return "+0%"
        # Decimal で正確な四捨五入を行う
        d = Decimal(str(value))
        # 指定桁数へ四捨五入
        quantize_str = "1" if decimals == 0 else "0." + "0" * decimals
        rounded = d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        # 符号付きフォーマット
        sign = "+" if rounded >= 0 else ""
        return f"{sign}{rounded}%"

    def _format_price(self, value: float | int | None) -> str:
        """株価フォーマット（整数なら整数、小数部あれば小数第1位まで四捨五入）

        日本株は0.5円刻みの値があるため、小数第1位を保持する。
        小数部が0なら整数として表示。

        Args:
            value: 数値

        Returns:
            フォーマット済み文字列（3桁カンマ区切り）
        """
        if value is None:
            return "0"
        # Decimal で正確な四捨五入を行う
        d = Decimal(str(value))
        # 小数第1位へ四捨五入
        rounded = d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        # 小数部が0なら整数として表示
        if rounded == rounded.to_integral_value():
            return f"{int(rounded):,}"
        return f"{rounded:,}"

    def _format_json(self, value: dict | list, indent: int = 2) -> str:
        """JSON整形

        Args:
            value: 辞書またはリスト
            indent: インデント幅

        Returns:
            整形済みJSON文字列
        """
        return json.dumps(value, ensure_ascii=False, indent=indent)
