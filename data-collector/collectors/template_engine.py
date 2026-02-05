"""Markdownテンプレートエンジンモジュール"""

import json

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

    def _format_currency(self, value: float | int) -> str:
        """通貨フォーマット（カンマ区切り）

        Args:
            value: 数値

        Returns:
            フォーマット済み文字列
        """
        return f"{value:,.0f}"

    def _format_number(self, value: float | int, decimals: int = 2) -> str:
        """数値フォーマット

        Args:
            value: 数値
            decimals: 小数点以下の桁数

        Returns:
            フォーマット済み文字列
        """
        if decimals == 0:
            return f"{value:,.0f}"
        return f"{value:,.{decimals}f}"

    def _format_percent(self, value: float | int, decimals: int = 1) -> str:
        """パーセントフォーマット

        Args:
            value: 数値（%の数値そのもの）
            decimals: 小数点以下の桁数

        Returns:
            フォーマット済み文字列（+記号付き）
        """
        return f"{value:+.{decimals}f}%"

    def _format_json(self, value: dict | list, indent: int = 2) -> str:
        """JSON整形

        Args:
            value: 辞書またはリスト
            indent: インデント幅

        Returns:
            整形済みJSON文字列
        """
        return json.dumps(value, ensure_ascii=False, indent=indent)
