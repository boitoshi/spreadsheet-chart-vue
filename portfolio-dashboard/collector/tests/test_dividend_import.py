"""collectors.dividend_import のユニットテスト。

DB・ネットワークには一切触れない（為替レートは Decimal のスタブ値を注入する）。
フィクスチャは実データの一部を模した数行の CSV テキストのみを使い、個人の
配当明細ファイルそのものはリポジトリにコミットしない。
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal

import pytest

from collectors.dividend_import import (
    AggregatedDividend,
    aggregate,
    build_save_record,
    parse_rakuten_csv,
)

# ────────────────────────────────────────────────────────────
# CSV フィクスチャ組み立てヘルパー
# ────────────────────────────────────────────────────────────

HEADER = [
    "入金日",
    "商品",
    "口座",
    "銘柄コード",
    "銘柄",
    "受取通貨",
    "単価[円/現地通貨]",
    "数量[株/口]",
    "配当・分配金合計（税引前）[円/現地通貨]",
    "税額合計[円/現地通貨]",
    "受取金額[円/現地通貨]",
]

# 実データの一部を模した数行（楽天証券の配当金明細と同じ体裁: 全列ダブルクォート）
SAMPLE_ROWS = [
    ["2026/06/29", "国内株式", "NISA成長投資枠", "2432", "ディー・エヌ・エー",
     "円", "-", "9", "594", "0", "594"],
    ["2026/06/29", "国内株式", "旧NISA", "7974", "任　天　堂",
     "円", "-", "1", "177", "0", "177"],
    ["2026/06/29", "国内株式", "NISA成長投資枠", "7974", "任　天　堂",
     "円", "-", "6", "1,062", "0", "1,062"],
    ["2026/06/29", "国内株式", "NISA成長投資枠", "7974", "任天堂",
     "円", "-", "0.61452701", "108", "0", "108"],
    ["2026/06/01", "国内株式", "NISA成長投資枠", "9432", "ＮＴＴ",
     "円", "-", "30", "80", "0", "80"],
    ["2026/06/30", "米国株式", "NISA成長投資枠", "NVDA", "NVIDIA CORP",
     "USドル", "0.25", "5", "1.25", "0", "1.12"],
]

# holdings に実際に登録されている銘柄コード（9432.T は未登録という想定）
HOLDINGS_CODES = {"7974.T", "2432.T", "NVDA"}


def _make_csv(rows: list[list[str]], header: list[str] | None = None) -> str:
    """テスト用 CSV テキストを組み立てる（QUOTE_ALL で実データと同じ体裁にする）。"""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow(header if header is not None else HEADER)
    writer.writerows(rows)
    return buf.getvalue()


# ────────────────────────────────────────────────────────────
# parse_rakuten_csv
# ────────────────────────────────────────────────────────────


def test_日付がスラッシュからハイフン区切りに変換される():
    text = _make_csv([SAMPLE_ROWS[0]])
    rows = parse_rakuten_csv(text)

    assert rows[0].date == "2026-06-29"


def test_国内株には銘柄コードにTが付与される():
    text = _make_csv([SAMPLE_ROWS[0]])
    rows = parse_rakuten_csv(text)

    assert rows[0].code == "2432.T"


def test_米国株の銘柄コードはそのまま():
    text = _make_csv([SAMPLE_ROWS[5]])
    rows = parse_rakuten_csv(text)

    assert rows[0].code == "NVDA"


def test_金額のカンマが除去されてDecimal化される():
    text = _make_csv([SAMPLE_ROWS[2]])  # "1,062"
    rows = parse_rakuten_csv(text)

    assert rows[0].total_pretax == Decimal("1062")


def test_想定外の商品区分は例外():
    row = ["2026/06/29", "投資信託", "特定", "1234", "謎の商品",
           "円", "-", "1", "100", "0", "100"]
    text = _make_csv([row])

    with pytest.raises(ValueError, match="想定外の商品区分"):
        parse_rakuten_csv(text)


def test_数値パース不能は例外():
    row = ["2026/06/29", "国内株式", "特定", "7974", "任天堂",
           "円", "-", "abc", "100", "0", "100"]
    text = _make_csv([row])

    with pytest.raises(ValueError):
        parse_rakuten_csv(text)


def test_日付パース不能は例外():
    row = ["2026-06-29", "国内株式", "特定", "7974", "任天堂",
           "円", "-", "1", "100", "0", "100"]
    text = _make_csv([row])

    with pytest.raises(ValueError):
        parse_rakuten_csv(text)


def test_必須ヘッダ列が欠けていると例外():
    broken_header = [h for h in HEADER if h != "銘柄コード"]
    text = _make_csv([SAMPLE_ROWS[0]], header=broken_header)

    with pytest.raises(ValueError, match="必須列"):
        parse_rakuten_csv(text)


def test_データ行が0行のCSVは空リストを返す():
    """ヘッダのみ（データ行なし）の CSV は例外にならず空リストが返る。"""
    text = _make_csv([])

    rows = parse_rakuten_csv(text)

    assert rows == []


def test_列が欠けた行は行番号つきValueErrorになる():
    """csv.DictReader は列が足りない行の欠損フィールドを restval="" で埋める
    （dividend_import.py の restval 指定による）。この指定が無いと欠損値が
    None のままになり、raw["銘柄コード"].strip() 等で AttributeError の
    素 traceback が出てしまう。ここでは行番号つきの ValueError に
    落ち着くことを確認する。
    """
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow(HEADER)
    # 「入金日」「商品」「口座」の3列しかない行（銘柄コード以降が欠損）
    writer.writerow(["2026/06/29", "国内株式", "特定"])
    text = buf.getvalue()

    with pytest.raises(ValueError, match=r"^1行目"):
        parse_rakuten_csv(text)


def test_cp932でエンコードした文字列を正しくデコードできる():
    """全角スペース入りの銘柄名（任　天　堂）を含む CSV が cp932 経由でも壊れない。"""
    text = _make_csv(SAMPLE_ROWS)
    # 実際の main.py は CSV ファイルを rb で読み cp932 でデコードする。
    # ここではファイルに依存せず、同じ往復をメモリ上で再現する。
    roundtripped = text.encode("cp932").decode("cp932")

    assert roundtripped == text

    rows = parse_rakuten_csv(roundtripped)
    nintendo_rows = [r for r in rows if r.code == "7974.T"]
    assert len(nintendo_rows) == 3


# ────────────────────────────────────────────────────────────
# aggregate
# ────────────────────────────────────────────────────────────


def test_端株は1株未満の端株として除外される():
    rows = parse_rakuten_csv(_make_csv(SAMPLE_ROWS))
    aggregated, skipped = aggregate(rows, HOLDINGS_CODES)

    fraction_skips = [s for s in skipped if s.reason == "1株未満の端株"]
    assert len(fraction_skips) == 1
    assert fraction_skips[0].shares == Decimal("0.61452701")


def test_1株以上の端数付き株数は仕様として投入される():
    """端株判定は「1株未満」のみが対象（aggregate の `shares < 1` 判定）。
    1.5株のような1株以上の端数は意図的にスキップせず投入する仕様であり、
    バグではないことをここで明文化する。
    """
    row = ["2026/07/01", "国内株式", "特定", "7974", "任天堂",
           "円", "-", "1.5", "150", "0", "150"]
    rows = parse_rakuten_csv(_make_csv([row]))

    aggregated, skipped = aggregate(rows, HOLDINGS_CODES)

    assert skipped == []
    assert len(aggregated) == 1
    assert aggregated[0].shares == Decimal("1.5")


def test_holdingsに無い銘柄は対象外として除外される():
    rows = parse_rakuten_csv(_make_csv(SAMPLE_ROWS))
    aggregated, skipped = aggregate(rows, HOLDINGS_CODES)

    ntt_skips = [s for s in skipped if s.code == "9432.T"]
    assert len(ntt_skips) == 1
    assert ntt_skips[0].reason == "holdings対象外"
    # 対象銘柄はハードコードしていないので、対象外判定は holdings_codes 由来
    assert "9432.T" not in {a.code for a in aggregated}


def test_同一日付コードの配当が合算される_7974Tの2026年6月29日実例():
    """1株177円 + 6株1,062円 = 7株1,239円（0.61452701株の端株行は合算に含めない）。"""
    rows = parse_rakuten_csv(_make_csv(SAMPLE_ROWS))
    aggregated, _skipped = aggregate(rows, HOLDINGS_CODES)

    target = next(
        a for a in aggregated if a.code == "7974.T" and a.date == "2026-06-29"
    )

    assert target.shares == Decimal("7")
    assert target.total_pretax == Decimal("1239")
    assert len(target.source_row_nos) == 2


def test_合算されない単独行はsource_row_nosが1件():
    rows = parse_rakuten_csv(_make_csv(SAMPLE_ROWS))
    aggregated, _skipped = aggregate(rows, HOLDINGS_CODES)

    nvda = next(a for a in aggregated if a.code == "NVDA")
    assert len(nvda.source_row_nos) == 1


# ────────────────────────────────────────────────────────────
# build_save_record
# ────────────────────────────────────────────────────────────


def test_国内株はtotal_jpyがそのまま整数化される():
    agg = AggregatedDividend(
        date="2026-06-29",
        code="7974.T",
        shares=Decimal("7"),
        total_pretax=Decimal("1239"),
        source_row_nos=[2, 3],
    )
    record = build_save_record(agg, name="任天堂", currency="JPY", rate=None)

    assert record["total_jpy"] == 1239
    assert record["dividend_foreign"] is None
    assert record["total_foreign"] is None
    assert record["exchange_rate"] is None


def test_国内株で非整数total_pretaxはROUND_HALF_UPで丸められる():
    agg = AggregatedDividend(
        date="2026-01-01",
        code="7974.T",
        shares=Decimal("1"),
        total_pretax=Decimal("100.5"),
        source_row_nos=[1],
    )
    record = build_save_record(agg, name="任天堂", currency="JPY", rate=None)

    assert record["total_jpy"] == 101


def test_外国株の円換算がROUND_HALF_UPで丸められる_5ちょうどの境界値():
    """総額(1.00) × レート(10.5) = 10.5円 → ROUND_HALF_UP で 11円。

    Python の組み込み round() は偶数丸め（銀行丸め）のため 10.5 → 10 になるが、
    このモジュールは ROUND_HALF_UP を使うため 11 になるべき境界値。
    """
    agg = AggregatedDividend(
        date="2026-06-30",
        code="NVDA",
        shares=Decimal("1"),
        total_pretax=Decimal("1.00"),
        source_row_nos=[6],
    )
    record = build_save_record(
        agg, name="エヌビディア", currency="USD", rate=Decimal("10.5")
    )

    assert record["total_jpy"] == 11


def test_外国株のdividend_foreignはtotalをsharesで割った導出値():
    agg = AggregatedDividend(
        date="2026-06-30",
        code="NVDA",
        shares=Decimal("5"),
        total_pretax=Decimal("1.25"),
        source_row_nos=[6],
    )
    record = build_save_record(
        agg, name="エヌビディア", currency="USD", rate=Decimal("155.0")
    )

    assert record["dividend_foreign"] == pytest.approx(0.25)
    assert record["total_foreign"] == pytest.approx(1.25)
    assert record["exchange_rate"] == pytest.approx(155.0)
    # 1.25 * 155.0 = 193.75 → ROUND_HALF_UP で 194
    assert record["total_jpy"] == 194


def test_外国株でrateがNoneならValueError():
    agg = AggregatedDividend(
        date="2026-06-30",
        code="NVDA",
        shares=Decimal("1"),
        total_pretax=Decimal("1.00"),
        source_row_nos=[6],
    )

    with pytest.raises(ValueError):
        build_save_record(agg, name="エヌビディア", currency="USD", rate=None)
