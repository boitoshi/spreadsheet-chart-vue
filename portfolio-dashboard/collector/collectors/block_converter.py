"""WordPress Gutenberg ブロック変換モジュール"""

from __future__ import annotations

import re


class GutenbergBlockConverter:
    """HTML を WordPress Gutenberg ブロック形式に変換するクラス。

    Python `markdown` ライブラリが生成する素の HTML を、
    WordPress Gutenberg ブロックコメント付き HTML に変換する。
    """

    # 複数行要素のプレースホルダー管理
    _PLACEHOLDER_PREFIX = "\x00BLOCK_PLACEHOLDER_"
    _PLACEHOLDER_SUFFIX = "\x00"

    # ブロックレベル要素の開始タグパターン
    _BLOCK_TAGS = re.compile(
        r"^<(?:h[1-6]|p|ul|ol|hr|img|blockquote|pre|div|figure|details)[\s>/]",
        re.IGNORECASE,
    )

    def convert(self, html: str) -> str:
        """素の HTML を Gutenberg ブロックコメント付き HTML に変換する。

        Args:
            html: Python markdown ライブラリが生成した素の HTML 文字列

        Returns:
            Gutenberg ブロックコメントでラップされた HTML 文字列
        """
        placeholders: dict[str, str] = {}

        # Step 1: 複数行にわたる要素をプレースホルダーに置換
        html = self._extract_multiline_blocks(html, placeholders)

        # Step 2: ブロックレベル要素の境界で分割
        raw_blocks = self._split_into_blocks(html)

        # Step 3: 各ブロックを Gutenberg 形式に変換
        converted_blocks: list[str] = []
        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            if self._PLACEHOLDER_PREFIX in block:
                converted_blocks.append(
                    self._restore_placeholders(block, placeholders)
                )
            else:
                converted_blocks.append(self._convert_block(block))

        return "\n\n".join(converted_blocks)

    def _split_into_blocks(self, html: str) -> list[str]:
        """HTML をブロックレベル要素の境界で分割する。

        markdown ライブラリは要素間を \\n 1つで区切るため、
        ブロックレベルタグの開始位置を検出して分割する。

        Args:
            html: 分割対象の HTML 文字列

        Returns:
            ブロック単位に分割された HTML 文字列のリスト
        """
        blocks: list[str] = []
        current_lines: list[str] = []

        for line in html.strip().split("\n"):
            # ブロックレベル要素の開始タグまたはプレースホルダーを検出
            if (
                self._BLOCK_TAGS.match(line.strip())
                or line.strip().startswith(self._PLACEHOLDER_PREFIX)
            ) and current_lines:
                blocks.append("\n".join(current_lines))
                current_lines = []
            current_lines.append(line)

        if current_lines:
            blocks.append("\n".join(current_lines))

        return blocks

    # ------------------------------------------------------------------
    # 内部メソッド
    # ------------------------------------------------------------------

    def _extract_multiline_blocks(
        self, html: str, placeholders: dict[str, str]
    ) -> str:
        """複数行要素（table, div.huki-box, details）をプレースホルダーに置換する。

        Args:
            html: 処理対象の HTML 文字列
            placeholders: プレースホルダー → 変換済みブロックの辞書（破壊的変更）

        Returns:
            プレースホルダー置換後の HTML 文字列
        """
        counter = [0]  # ネストされた関数から変更するためリストを使用

        def replace_block(pattern: str, convert_fn) -> None:
            nonlocal html
            # re.DOTALL で複数行にまたがるブロックを取得
            def replacer(m: re.Match) -> str:
                key = (
                    f"{self._PLACEHOLDER_PREFIX}{counter[0]}"
                    f"{self._PLACEHOLDER_SUFFIX}"
                )
                counter[0] += 1
                placeholders[key] = convert_fn(m.group(0))
                return key

            html = re.sub(pattern, replacer, html, flags=re.DOTALL | re.IGNORECASE)

        # table ブロックを抽出・変換
        replace_block(r"<table[\s\S]*?</table>", self._convert_table)

        # div.huki-box ブロックを抽出・変換
        # huki-box は内部に 2 つの div がネストされるため、
        # 3 つ目の </div> が外側の閉じタグになる
        replace_block(
            r'<div\s+class="huki-box[^"]*">(?:[\s\S]*?</div>){3}',
            self._convert_huki_box,
        )

        # details ブロックを抽出・変換（購入履歴の折りたたみ）
        replace_block(
            r"<details[\s\S]*?</details>",
            self._convert_details,
        )

        return html

    def _restore_placeholders(
        self, block: str, placeholders: dict[str, str]
    ) -> str:
        """プレースホルダーを変換済みブロックに復元する。

        Args:
            block: プレースホルダーを含むブロック文字列
            placeholders: プレースホルダー → 変換済みブロックの辞書

        Returns:
            プレースホルダーを復元したブロック文字列
        """
        for key, value in placeholders.items():
            block = block.replace(key, value)
        return block

    def _convert_block(self, block: str) -> str:
        """1つの HTML ブロックを対応する Gutenberg ブロック形式に変換する。

        Args:
            block: 変換対象の HTML ブロック文字列（1要素分）

        Returns:
            Gutenberg ブロックコメントでラップされた HTML 文字列
        """
        stripped = block.strip()

        # 見出し: <h1> ~ <h6>
        m = re.match(r"^<h([1-6])(\s[^>]*)?>", stripped, re.IGNORECASE)
        if m:
            return self._convert_heading(stripped, int(m.group(1)))

        # 段落: <p>
        if re.match(r"^<p(\s|>)", stripped, re.IGNORECASE):
            return f"<!-- wp:paragraph -->\n{stripped}\n<!-- /wp:paragraph -->"

        # 順序なしリスト: <ul>
        if re.match(r"^<ul(\s|>)", stripped, re.IGNORECASE):
            return f"<!-- wp:list -->\n{stripped}\n<!-- /wp:list -->"

        # 順序付きリスト: <ol>
        if re.match(r"^<ol(\s|>)", stripped, re.IGNORECASE):
            return (
                f'<!-- wp:list {{"ordered":true}} -->\n'
                f"{stripped}\n"
                f"<!-- /wp:list -->"
            )

        # 画像: <img ...>
        if re.match(r"^<img(\s|>|/>)", stripped, re.IGNORECASE):
            return self._convert_image(stripped)

        # 水平線: <hr>, <hr/>, <hr />
        if re.match(r"^<hr\s*/?>\s*$", stripped, re.IGNORECASE):
            return (
                "<!-- wp:separator -->\n"
                '<hr class="wp-block-separator"/>\n'
                "<!-- /wp:separator -->"
            )

        # その他
        return f"<!-- wp:html -->\n{stripped}\n<!-- /wp:html -->"

    def _convert_heading(self, block: str, level: int) -> str:
        """見出し要素を Gutenberg heading ブロックに変換する。

        class="wp-block-heading" 属性を追加し、ブロックコメントでラップする。

        Args:
            block: 変換対象の見出し HTML 文字列
            level: 見出しレベル（1〜6）

        Returns:
            Gutenberg heading ブロック形式の文字列
        """
        # 既存の class 属性があれば wp-block-heading を追加、なければ新規付与
        if re.search(rf"<h{level}\s[^>]*class=", block, re.IGNORECASE):
            # 既存 class 属性に wp-block-heading を追加
            converted = re.sub(
                rf'(<h{level}[^>]*class=")([^"]*)"',
                r'\1\2 wp-block-heading"',
                block,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            # class 属性を新規追加
            converted = re.sub(
                rf"(<h{level})(\s[^>]*)?>",
                rf'<h{level} class="wp-block-heading">',
                block,
                count=1,
                flags=re.IGNORECASE,
            )

        return (
            f'<!-- wp:heading {{"level":{level}}} -->\n'
            f"{converted}\n"
            f"<!-- /wp:heading -->"
        )

    def _convert_table(self, table_html: str) -> str:
        """table 要素を Gutenberg table ブロックに変換する。

        <table> に class="has-fixed-layout" を付与し、
        <figure class="wp-block-table is-style-table-pop"> でラップする。

        Args:
            table_html: 変換対象の <table>...</table> HTML 文字列

        Returns:
            Gutenberg table ブロック形式の文字列
        """
        # <table> タグに class="has-fixed-layout" を付与
        converted = re.sub(
            r"<table(\s[^>]*)?>",
            '<table class="has-fixed-layout">',
            table_html,
            count=1,
            flags=re.IGNORECASE,
        )

        figure = (
            f'<figure class="wp-block-table is-style-table-pop">'
            f"{converted}"
            f"</figure>"
        )

        return (
            '<!-- wp:table {"className":"is-style-table-pop"} -->\n'
            f"{figure}\n"
            "<!-- /wp:table -->"
        )

    def _convert_image(self, img_html: str) -> str:
        """img 要素を Gutenberg image ブロックに変換する。

        <figure class="wp-block-image size-full"> でラップする。

        Args:
            img_html: 変換対象の <img .../> HTML 文字列

        Returns:
            Gutenberg image ブロック形式の文字列
        """
        figure = f'<figure class="wp-block-image size-full">{img_html}</figure>'
        return f"<!-- wp:image -->\n{figure}\n<!-- /wp:image -->"

    def _convert_huki_box(self, div_html: str) -> str:
        """huki-box div 要素を Gutenberg html ブロックに変換する。

        Args:
            div_html: 変換対象の <div class="huki-box ...">...</div> HTML 文字列

        Returns:
            Gutenberg html ブロック形式の文字列
        """
        return f"<!-- wp:html -->\n{div_html}\n<!-- /wp:html -->"

    def _convert_details(self, details_html: str) -> str:
        """details 要素を Gutenberg html ブロックに変換する。

        Args:
            details_html: 変換対象の <details>...</details> HTML 文字列

        Returns:
            Gutenberg html ブロック形式の文字列
        """
        return f"<!-- wp:html -->\n{details_html}\n<!-- /wp:html -->"
