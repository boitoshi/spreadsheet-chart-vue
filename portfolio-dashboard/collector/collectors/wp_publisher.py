"""WordPress REST API 投稿モジュール（月次投資ブログ用）"""

from __future__ import annotations

from pathlib import Path

import markdown
import requests

from .block_converter import GutenbergBlockConverter

_SECTION_START_PREFIX = "<!-- pokebros-monthly-section:start:"
_SECTION_END_PREFIX = "<!-- pokebros-monthly-section:end:"
_SECTION_SUFFIX = " -->"


def _marker_id(line: str, prefix: str) -> str | None:
    """明示的な月次ブログセクションマーカーからIDを取り出す。"""
    stripped = line.strip()
    if not stripped.startswith(prefix) or not stripped.endswith(_SECTION_SUFFIX):
        return None
    section_id = stripped[len(prefix) : -len(_SECTION_SUFFIX)]
    return section_id or None


def _parse_marked_sections(content: str) -> list[tuple[str, str]]:
    """行単位の明示マーカーでコンテンツを構造化セクションへ分ける。"""
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()
    current_id: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        start_id = _marker_id(line, _SECTION_START_PREFIX)
        end_id = _marker_id(line, _SECTION_END_PREFIX)
        if start_id is not None:
            if current_id is not None:
                raise ValueError("月次ブログのセクションマーカーが入れ子です")
            if start_id in seen:
                raise ValueError(f"月次ブログのセクションが重複しています: {start_id}")
            current_id = start_id
            current_lines = []
            continue
        if end_id is not None:
            if current_id != end_id:
                raise ValueError(
                    "月次ブログのセクション終了マーカーが対応していません"
                )
            assert current_id is not None
            section_content = "\n".join(current_lines).strip()
            sections.append((current_id, section_content))
            seen.add(current_id)
            current_id = None
            current_lines = []
            continue
        if current_id is not None:
            current_lines.append(line)
        elif line.strip():
            raise ValueError("月次ブログのセクション外にコンテンツがあります")

    if current_id is not None:
        raise ValueError(f"月次ブログの終了マーカーがありません: {current_id}")
    if not sections:
        raise ValueError("月次ブログのセクションがありません")
    return sections


def _to_gutenberg(markdown_content: str) -> str:
    """MarkdownセクションをGutenbergの標準ブロックへ変換する。"""
    if not markdown_content.strip():
        return ""
    html_content = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code"],
    )
    return GutenbergBlockConverter().convert(html_content)


def _html_block(content: str) -> str:
    """自己完結したHTMLセクションをwp:htmlブロックで包む。"""
    return f"<!-- wp:html -->\n{content}\n<!-- /wp:html -->"


def _compose_native_sections(markdown_content: str) -> str:
    """月次Markdownだけをマーカー順の標準ブロックへ変換する。"""
    sections = _parse_marked_sections(markdown_content)
    if any(not section_id.startswith("native-") for section_id, _ in sections):
        raise ValueError("月次ブログMarkdownにHTMLセクションが混在しています")
    return "\n\n".join(
        block
        for _section_id, content in sections
        if (block := _to_gutenberg(content))
    )


def compose_monthly_blog_content(
    markdown_content: str, raw_html_prepend: str
) -> str:
    """月次ブログのHTMLカードと標準コメントブロックを交互に並べる。"""
    html_sections = _parse_marked_sections(raw_html_prepend)
    native_sections = _parse_marked_sections(markdown_content)
    html_by_id = dict(html_sections)
    native_by_id = dict(native_sections)

    required_html = {"html-overview", "html-script"}
    required_native = {"native-intro", "native-tail"}
    if not required_html.issubset(html_by_id):
        raise ValueError("月次ブログの概要またはスクリプトがありません")
    if not required_native.issubset(native_by_id):
        raise ValueError("月次ブログの振り返りまたは末尾セクションがありません")

    stock_html_ids = [
        section_id
        for section_id, _content in html_sections
        if section_id.startswith("html-stock:")
    ]
    allowed_html = required_html | set(stock_html_ids)
    if set(html_by_id) != allowed_html:
        raise ValueError("月次ブログHTMLに未対応のセクションがあります")

    stock_codes = {
        section_id.removeprefix("html-stock:") for section_id in stock_html_ids
    }
    native_stock_codes = {
        section_id.removeprefix("native-stock:")
        for section_id in native_by_id
        if section_id.startswith("native-stock:")
    }
    if not native_stock_codes.issubset(stock_codes):
        raise ValueError("対応する銘柄カードがない振り返りがあります")
    allowed_native = required_native | {
        f"native-stock:{code}" for code in native_stock_codes
    }
    if set(native_by_id) != allowed_native:
        raise ValueError("月次ブログMarkdownに未対応のセクションがあります")

    blocks = [_html_block(html_by_id["html-overview"])]
    intro_block = _to_gutenberg(native_by_id["native-intro"])
    if intro_block:
        blocks.append(intro_block)

    for html_id in stock_html_ids:
        code = html_id.removeprefix("html-stock:")
        blocks.append(_html_block(html_by_id[html_id]))
        comment_block = _to_gutenberg(
            native_by_id.get(f"native-stock:{code}", "")
        )
        if comment_block:
            blocks.append(comment_block)

    tail_block = _to_gutenberg(native_by_id["native-tail"])
    if tail_block:
        blocks.append(tail_block)
    blocks.append(_html_block(html_by_id["html-script"]))
    return "\n\n".join(blocks)


class WpPublisher:
    """WordPress REST API を使って月次投資ブログを下書き投稿するクラス。

    認証は Application Password を使用する。
    WordPress 管理画面 → ユーザー → プロフィール → アプリケーションパスワード で発行。
    """

    def __init__(self, wp_url: str, wp_user: str, wp_app_password: str) -> None:
        """初期化

        Args:
            wp_url: WordPress サイトの URL（末尾スラッシュ不要）
            wp_user: WordPress ユーザー名
            wp_app_password: Application Password（スペース込みでも可）
        """
        self.wp_url = wp_url.rstrip("/")
        self.auth = (wp_user, wp_app_password)

    def upload_image(self, image_path: str) -> int:
        """画像ファイルを WordPress メディアライブラリにアップロードする。

        Args:
            image_path: アップロードする画像ファイルのパス

        Returns:
            WordPress メディア ID

        Raises:
            FileNotFoundError: 画像ファイルが存在しない場合
            requests.HTTPError: API リクエストが失敗した場合
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(
                f"画像ファイルが見つかりません: {image_path}"
            )

        # MIME タイプをサフィックスから判定（PNG/JPEG/GIF 対応）
        suffix = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }
        mime_type = mime_map.get(suffix, "application/octet-stream")

        print(f"  画像アップロード中: {path.name}")
        with open(path, "rb") as f:
            resp = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/media",
                auth=self.auth,
                headers={"Content-Disposition": f"attachment; filename={path.name}"},
                files={"file": (path.name, f, mime_type)},
                timeout=60,
            )

        if not resp.ok:
            print(
                f"  [エラー] 画像アップロード失敗: {path.name} "
                f"(HTTP {resp.status_code}: {resp.text[:200]})"
            )
            resp.raise_for_status()

        media_id: int = resp.json()["id"]
        print(f"  画像アップロード完了: {path.name} → メディア ID {media_id}")
        return media_id

    def create_draft(
        self,
        title: str,
        markdown_content: str,
        image_paths: list[str] | None = None,
        slug: str | None = None,
        raw_html_prepend: str | None = None,
        categories: list[int] | None = None,
        date: str | None = None,
    ) -> str:
        """Markdown コンテンツを HTML に変換し、WordPress に下書き投稿する。

        画像パスが指定された場合はメディアライブラリにアップロードし、
        Markdown 内のファイル名を WordPress の配信 URL に置換する。

        Args:
            title: 投稿タイトル
            markdown_content: Markdown 形式の本文
            image_paths: アップロードする画像ファイルのパスリスト（省略可）
            slug: 投稿のスラッグ（URL パーマリンク用）。
                省略時は WordPress が自動生成する
            raw_html_prepend: Gutenberg 変換前に本文先頭に追加する生 HTML 文字列。
                月次セクションマーカー付きならMarkdownの振り返りと交互に配置し、
                それ以外は単一の <!-- wp:html --> ブロックとして本文先頭へ置く
            categories: 投稿に付けるカテゴリ ID のリスト（省略可）
            date: 投稿日（サイトのローカル時刻、形式 "YYYY-MM-DDTHH:MM:SS"）。
                省略時は実行日の日付で下書きが作成される

        Returns:
            作成された下書き投稿の URL

        Raises:
            requests.HTTPError: API リクエストが失敗した場合
        """
        if image_paths is None:
            image_paths = []

        # 1. 画像をアップロードし、Markdown 内のファイル名を WordPress URL に置換
        for img_path in image_paths:
            try:
                media_id = self.upload_image(img_path)
            except FileNotFoundError as e:
                print(f"  [警告] 画像をスキップします: {e}")
                continue
            except requests.HTTPError:
                print(f"  [警告] 画像アップロードをスキップします: {img_path}")
                continue

            # メディア URL を取得して Markdown 内の参照を置換
            try:
                media_resp = requests.get(
                    f"{self.wp_url}/wp-json/wp/v2/media/{media_id}",
                    auth=self.auth,
                    timeout=30,
                )
                media_resp.raise_for_status()
                wp_source_url: str = media_resp.json()["source_url"]
                img_name = Path(img_path).name
                markdown_content = markdown_content.replace(img_name, wp_source_url)
                print(f"  URL 置換完了: {img_name} → {wp_source_url}")
            except requests.HTTPError as e:
                print(
                    f"  [警告] メディア URL の取得に失敗しました (ID={media_id}): {e}"
                )

        # 2. Markdown / 埋め込みHTML → Gutenberg ブロック変換
        has_html_markers = (
            raw_html_prepend is not None
            and _SECTION_START_PREFIX in raw_html_prepend
        )
        has_native_markers = _SECTION_START_PREFIX in markdown_content
        if has_html_markers:
            assert raw_html_prepend is not None
            html_content = compose_monthly_blog_content(
                markdown_content, raw_html_prepend
            )
        else:
            # マーカー付きfragmentがなければ、HTMLは従来どおり本文先頭へ置く。
            html_content = (
                _compose_native_sections(markdown_content)
                if has_native_markers
                else _to_gutenberg(markdown_content)
            )
            if raw_html_prepend:
                html_content = (
                    f"{_html_block(raw_html_prepend)}\n\n{html_content}"
                )

        # 3. WordPress に下書きとして POST
        print(f"  WordPress に下書き投稿中: 「{title}」")
        body: dict = {
            "title": title,
            "content": html_content,
            "status": "draft",
        }
        if slug:
            body["slug"] = slug
        if categories:
            body["categories"] = categories
        if date:
            body["date"] = date
        resp = requests.post(
            f"{self.wp_url}/wp-json/wp/v2/posts",
            auth=self.auth,
            json=body,
            timeout=60,
        )

        if not resp.ok:
            print(
                f"  [エラー] 投稿失敗: HTTP {resp.status_code}: {resp.text[:200]}"
            )
            resp.raise_for_status()

        post_link: str = resp.json()["link"]
        print(f"  下書き投稿完了: {post_link}")
        return post_link
