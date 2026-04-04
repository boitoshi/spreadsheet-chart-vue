"""WordPress REST API 投稿モジュール（月次投資ブログ用）"""

from __future__ import annotations

from pathlib import Path

import markdown
import requests


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
    ) -> str:
        """Markdown コンテンツを HTML に変換し、WordPress に下書き投稿する。

        画像パスが指定された場合はメディアライブラリにアップロードし、
        Markdown 内のファイル名を WordPress の配信 URL に置換する。

        Args:
            title: 投稿タイトル
            markdown_content: Markdown 形式の本文
            image_paths: アップロードする画像ファイルのパスリスト（省略可）

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

        # 2. Markdown → HTML 変換（テーブル・コードブロック拡張を有効化）
        html_content = markdown.markdown(
            markdown_content,
            extensions=["tables", "fenced_code"],
        )

        # 3. WordPress に下書きとして POST
        print(f"  WordPress に下書き投稿中: 「{title}」")
        resp = requests.post(
            f"{self.wp_url}/wp-json/wp/v2/posts",
            auth=self.auth,
            json={
                "title": title,
                "content": html_content,
                "status": "draft",
            },
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
