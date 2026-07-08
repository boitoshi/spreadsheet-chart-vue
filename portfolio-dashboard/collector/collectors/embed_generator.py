"""ブログ埋め込み HTML / JSON エクスポートモジュール。

report_json_builder で構築した ReportData を
templates/blog_embed.html を用いて standalone / fragment の2モードで出力する。
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from .report_json_builder import build_report_data
from .template_engine import MarkdownTemplateEngine

if TYPE_CHECKING:
    from .db_writer import DbWriter

# output/embeds/ への保存先ディレクトリ
_OUTPUT_DIR_NAME = "embeds"


class EmbedGenerator:
    """月次レポート埋め込みコンテンツを生成するクラス。

    処理フロー:
        1. report_json_builder.build_report_data で DB からデータを構築
        2. output/embeds/portfolio_{year}_{month:02d}.json に保存
        3. templates/blog_embed.html で standalone HTML を生成・保存
        4. 同テンプレートで fragment HTML を生成・保存
    """

    def __init__(
        self,
        db: DbWriter,
        output_dir: str,
        template_dir: str,
    ) -> None:
        """初期化。

        Args:
            db: DbWriter インスタンス
            output_dir: output/ ディレクトリの絶対パス
            template_dir: templates/ ディレクトリの絶対パス
        """
        self.db = db
        self.embeds_dir = os.path.join(output_dir, _OUTPUT_DIR_NAME)
        self.engine = MarkdownTemplateEngine(template_dir=template_dir)

    def generate(self, year: int, month: int) -> dict | None:
        """指定月の埋め込みコンテンツを生成する。

        Args:
            year: 年
            month: 月

        Returns:
            成功時は生成した ReportData 辞書（build_report_data の戻り値）。
            データが存在しない場合は None。

        Side effects:
            output/embeds/portfolio_{year}_{month:02d}.json を保存
            output/embeds/blog_embed_{year}_{month:02d}.html（standalone）を保存
            output/embeds/blog_embed_{year}_{month:02d}_fragment.html を保存
        """
        target_date = f"{year}-{month:02d}-末"
        report_data = build_report_data(self.db, target_date)

        if report_data is None:
            print(
                f"  [埋め込み] {year}年{month}月のデータが見つかりません。スキップ。"
            )
            return None

        os.makedirs(self.embeds_dir, exist_ok=True)

        # JSON 保存
        json_path = os.path.join(
            self.embeds_dir, f"portfolio_{year}_{month:02d}.json"
        )
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"  [埋め込み] JSON 保存: {json_path}")

        # standalone HTML 保存
        standalone_html = self.engine.render(
            "blog_embed.html",
            {"data": report_data, "standalone": True},
        )
        standalone_path = os.path.join(
            self.embeds_dir, f"blog_embed_{year}_{month:02d}.html"
        )
        with open(standalone_path, "w", encoding="utf-8") as f:
            f.write(standalone_html)
        print(f"  [埋め込み] standalone HTML 保存: {standalone_path}")

        # fragment HTML 保存
        fragment_html = self.engine.render(
            "blog_embed.html",
            {"data": report_data, "standalone": False},
        )
        fragment_path = os.path.join(
            self.embeds_dir, f"blog_embed_{year}_{month:02d}_fragment.html"
        )
        with open(fragment_path, "w", encoding="utf-8") as f:
            f.write(fragment_html)
        print(f"  [埋め込み] fragment HTML 保存: {fragment_path}")

        return report_data

    def get_fragment_content(self, year: int, month: int) -> str | None:
        """生成済み fragment HTML の内容を返す。

        generate() を先に呼ぶことを前提とする。

        Args:
            year: 年
            month: 月

        Returns:
            fragment HTML 文字列。ファイルが存在しない場合は None。
        """
        fragment_path = os.path.join(
            self.embeds_dir, f"blog_embed_{year}_{month:02d}_fragment.html"
        )
        if not os.path.exists(fragment_path):
            return None
        with open(fragment_path, encoding="utf-8") as f:
            return f.read()
