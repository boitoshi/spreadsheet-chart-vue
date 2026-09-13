"""AI コメントの保存と再生成判定のテスト。"""

from __future__ import annotations

from types import SimpleNamespace

from main import (
    PortfolioDataCollector,
    _has_complete_ai_comments,
)

REPORT_DATA = {
    "holdings": [
        {"symbol": "7974.T"},
        {"symbol": "NVDA"},
    ]
}


def test_incomplete_saved_comments_are_regenerated() -> None:
    complete = {
        ("", "intro"): "導入です。",
        ("7974.T", "stock"): "任天堂です。",
        ("NVDA", "stock"): "NVIDIAです。",
    }
    missing_intro = {
        key: value for key, value in complete.items() if key != ("", "intro")
    }
    missing_stock = {
        key: value for key, value in complete.items() if key != ("NVDA", "stock")
    }

    assert _has_complete_ai_comments(complete, REPORT_DATA)
    assert not _has_complete_ai_comments(missing_intro, REPORT_DATA)
    assert not _has_complete_ai_comments(missing_stock, REPORT_DATA)


def test_empty_comments_are_not_saved_and_warning_is_printed(capsys) -> None:
    collector = PortfolioDataCollector.__new__(PortfolioDataCollector)
    collector.db_writer = SimpleNamespace(save_ai_comment=lambda *args: None)

    saved = collector._save_ai_comments(
        "2026-08-末", {"intro": None, "summary": None, "stock_comments": {}}
    )

    assert not saved
    assert "DB 保存をスキップ" in capsys.readouterr().out


def test_partial_comments_save_only_valid_content(capsys) -> None:
    calls: list[tuple] = []
    collector = PortfolioDataCollector.__new__(PortfolioDataCollector)
    collector.db_writer = SimpleNamespace(
        save_ai_comment=lambda *args: calls.append(args)
    )

    saved = collector._save_ai_comments(
        "2026-08-末",
        {
            "intro": "導入です。",
            "summary": None,
            "stock_comments": {"7974.T": "任天堂です。"},
        },
    )

    assert saved
    assert calls == [
        ("2026-08-末", "7974.T", "stock", "任天堂です。"),
        ("2026-08-末", "", "intro", "導入です。"),
    ]
    assert "DB に保存しました" in capsys.readouterr().out
