import re
from pathlib import Path

# data-collector/output/ への絶対パス
_OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data-collector"
    / "output"
)


def list_reports() -> list[dict]:
    """output/ 内の blog_draft_*.md ファイル一覧を返す（降順）"""
    if not _OUTPUT_DIR.exists():
        return []
    pattern = re.compile(r"blog_draft_(\d{4})_(\d{2})\.md$")
    reports = []
    for f in _OUTPUT_DIR.glob("blog_draft_*.md"):
        m = pattern.match(f.name)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            reports.append({
                "year": year,
                "month": month,
                "label": f"{year}年{month}月",
                "filename": f.name,
            })
    return sorted(reports, key=lambda r: (r["year"], r["month"]), reverse=True)


def read_report(year: int, month: int) -> str | None:
    """指定年月の blog_draft を読み込んで返す。存在しない場合は None"""
    path = _OUTPUT_DIR / f"blog_draft_{year}_{month:02d}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
