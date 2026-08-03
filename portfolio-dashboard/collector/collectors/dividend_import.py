"""楽天証券の配当金明細CSVをパースし、dividends テーブル保存用レコードを
組み立てる純粋関数モジュール。

DB・ネットワークに一切依存しない stdlib のみの実装。main.py の
import_dividends が本モジュールの関数を呼び出し、DB 書き込み・為替レート取得
（ネットワーク I/O）を担当する薄いラッパーとなる。為替レートは呼び出し側から
引数として注入する（このモジュールはオフラインでテスト可能）。

データ規約:
- 楽天証券の CSV は cp932 エンコーディング、ヘッダ1行 + データ行
  （デコードは呼び出し側の責務。本モジュールはデコード済み文字列を受け取る）
- 「商品」列は「国内株式」「米国株式」の2種類のみを想定する。それ以外は
  想定外データとして例外を送出する（黙ってスキップしない）
- 金額・数量列に含まれるカンマ区切り（例: "1,062"）を除去してから
  Decimal 化する
- 使うのは「配当・分配金合計（税引前）」列（受取金額＝税引後ではない）
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import StringIO

# CSV に存在すべき必須ヘッダ列（列順には依存しない。DictReader で名前参照する）
REQUIRED_COLUMNS = (
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
)

# 商品区分 → 銘柄コード変換規則（この2種類以外は想定外として例外にする）
_DOMESTIC_PRODUCT = "国内株式"
_FOREIGN_PRODUCT = "米国株式"

_TOTAL_PRETAX_COLUMN = "配当・分配金合計（税引前）[円/現地通貨]"


@dataclass(frozen=True)
class DividendRow:
    """CSV 1行分をパースした結果。

    row_no: CSV のデータ行番号（1始まり。ヘッダを含まない。スキップ理由表示用）
    date: "YYYY-MM-DD" 形式
    code: 銘柄コード（国内株は ".T" 付与済み、外国株は CSV の値そのまま）
    currency: 受取通貨（CSV そのまま。例: "円", "USドル"。表示専用で、
        実際の通貨判定は holdings.currency を使う）
    shares: 数量（株/口）
    total_pretax: 配当・分配金合計（税引前）。受取通貨建て
    """

    row_no: int
    date: str
    code: str
    currency: str
    shares: Decimal
    total_pretax: Decimal


@dataclass(frozen=True)
class SkippedRow:
    """aggregate() でスキップされた行（理由付き）。"""

    row_no: int
    code: str
    reason: str
    shares: Decimal
    total_pretax: Decimal
    currency: str


@dataclass(frozen=True)
class AggregatedDividend:
    """(date, code) 単位で合算した配当レコード。

    dividends テーブルは date+code が UNIQUE のため、同一日に複数回受け取った
    配当（NISA枠と旧NISA枠に分かれて入金される等）は合算しないと後勝ちで
    消えてしまう。source_row_nos で元になった CSV 行番号が分かるようにする。
    """

    date: str
    code: str
    shares: Decimal
    total_pretax: Decimal
    source_row_nos: list[int]


def _parse_decimal(value: str, *, field_name: str, row_no: int) -> Decimal:
    """カンマ区切りを除去して Decimal 化する。パース不能なら ValueError。"""
    cleaned = value.replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation as e:
        raise ValueError(
            f"{row_no}行目: {field_name} の数値パースに失敗しました（値: {value!r}）"
        ) from e


def _parse_date(value: str, *, row_no: int) -> str:
    """"2026/06/29" → "2026-06-29" に変換する。

    datetime.strptime で実在する日付かどうかも検証する（"2026/13/45" の
    ような区切りは3つだが実在しない日付を弾くため）。パース不能・
    実在しない日付なら ValueError。
    """
    try:
        dt = datetime.strptime(value.strip(), "%Y/%m/%d")
    except ValueError as e:
        raise ValueError(
            f"{row_no}行目: 入金日のパースに失敗しました（値: {value!r}）"
        ) from e
    return dt.strftime("%Y-%m-%d")


def parse_rakuten_csv(text: str) -> list[DividendRow]:
    """楽天証券の配当金明細 CSV（デコード済み文字列）をパースする。

    Args:
        text: cp932 デコード済みの CSV 全文。

    Returns:
        DividendRow のリスト（CSV 記載順）。

    Raises:
        ValueError: ヘッダが無い、必須列が欠けている、商品区分が
            「国内株式」「米国株式」以外、日付・数値のパースに失敗した場合。
    """
    # restval="" を指定し、列が足りない行でも値を None ではなく空文字列にする。
    # None のままだと raw["銘柄コード"].strip() 等が AttributeError を投げて
    # 素の traceback で落ちてしまうため（空文字列なら後続の ValueError に
    # 正しく落とし込める）
    reader = csv.DictReader(StringIO(text), restval="")
    if reader.fieldnames is None:
        raise ValueError("CSV にヘッダ行がありません")
    missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"CSV に必須列がありません: {', '.join(missing)}")

    rows: list[DividendRow] = []
    for row_no, raw in enumerate(reader, start=1):
        product = raw["商品"]
        raw_code = raw["銘柄コード"].strip()
        if product == _DOMESTIC_PRODUCT:
            code = f"{raw_code}.T"
        elif product == _FOREIGN_PRODUCT:
            code = raw_code
        else:
            raise ValueError(
                f"{row_no}行目: 想定外の商品区分です（{product!r}）。"
                f"「{_DOMESTIC_PRODUCT}」「{_FOREIGN_PRODUCT}」以外は未対応です"
            )

        date = _parse_date(raw["入金日"], row_no=row_no)
        shares = _parse_decimal(raw["数量[株/口]"], field_name="数量", row_no=row_no)
        total_pretax = _parse_decimal(
            raw[_TOTAL_PRETAX_COLUMN],
            field_name="配当・分配金合計（税引前）",
            row_no=row_no,
        )

        rows.append(
            DividendRow(
                row_no=row_no,
                date=date,
                code=code,
                currency=raw["受取通貨"].strip(),
                shares=shares,
                total_pretax=total_pretax,
            )
        )

    return rows


def aggregate(
    rows: list[DividendRow], holdings_codes: set[str]
) -> tuple[list[AggregatedDividend], list[SkippedRow]]:
    """パース済み行を対象外・端株でスキップしたうえで (date, code) 単位に合算する。

    対象銘柄はハードコードしない。holdings_codes に無い銘柄は「holdings 対象外」
    として落とすため、将来 holdings に銘柄が増えても本関数の変更は不要。

    Args:
        rows: parse_rakuten_csv() の戻り値。
        holdings_codes: holdings テーブルに存在する銘柄コードの集合。

    Returns:
        (合算後レコードのリスト, スキップ行のリスト) のタプル。
        合算後レコードは (date, code) の初出順。
    """
    grouped: dict[tuple[str, str], list[DividendRow]] = {}
    skipped: list[SkippedRow] = []

    for row in rows:
        if row.code not in holdings_codes:
            skipped.append(
                SkippedRow(
                    row_no=row.row_no,
                    code=row.code,
                    reason="holdings対象外",
                    shares=row.shares,
                    total_pretax=row.total_pretax,
                    currency=row.currency,
                )
            )
            continue
        if row.shares < 1:
            skipped.append(
                SkippedRow(
                    row_no=row.row_no,
                    code=row.code,
                    reason="1株未満の端株",
                    shares=row.shares,
                    total_pretax=row.total_pretax,
                    currency=row.currency,
                )
            )
            continue
        grouped.setdefault((row.date, row.code), []).append(row)

    aggregated = [
        AggregatedDividend(
            date=date,
            code=code,
            shares=sum((r.shares for r in group), Decimal(0)),
            total_pretax=sum((r.total_pretax for r in group), Decimal(0)),
            source_row_nos=[r.row_no for r in group],
        )
        for (date, code), group in grouped.items()
    ]

    return aggregated, skipped


def build_save_record(
    agg: AggregatedDividend, *, name: str, currency: str, rate: Decimal | None
) -> dict:
    """合算済みレコードから db_writer.save_dividend にそのまま渡せる dict を組み立てる。

    Args:
        agg: aggregate() が返す合算済みレコード。
        name: 銘柄名（holdings 由来。CSV の表記ゆれ「任　天　堂」ではなく
            holdings.name を使うことで既存の配当データと表記を揃える）。
        currency: 通貨コード（holdings.currency。"JPY" ならその他フィールドは
            None、それ以外は外国株として扱う）。
        rate: 外国株の場合の受取日為替レート（USD/JPY 等、Decimal）。日本株
            なら未使用のため None で良い。呼び出し側で Decimal 化済みの値を
            渡す前提（2進浮動小数の誤差を持ち込まないため）。内部では念のため
            str() を経由してから乗算する。

    Returns:
        db_writer.save_dividend にそのまま渡せる dict
        （date, code, name, dividend_foreign, shares, total_foreign,
          currency, exchange_rate, total_jpy）。

    Raises:
        ValueError: 外国株（currency != "JPY"）で rate が None の場合。
    """
    shares_float = float(agg.shares)

    if currency == "JPY":
        total = agg.total_pretax
        if total == total.to_integral_value():
            total_jpy = int(total)
        else:
            total_jpy = int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return {
            "date": agg.date,
            "code": agg.code,
            "name": name,
            "dividend_foreign": None,
            "shares": shares_float,
            "total_foreign": None,
            "currency": currency,
            "exchange_rate": None,
            "total_jpy": total_jpy,
        }

    if rate is None:
        raise ValueError(
            f"外国株（code={agg.code!r}, date={agg.date!r}）に為替レートがありません"
        )

    # main.py の add_dividend（679〜683行目）と同一式。
    # dividend_foreign は total ÷ shares の導出参考値（total が正の値であり、
    # 1株配当×株数で総額を求めているわけではない点に注意）
    rate_dec = Decimal(str(rate))
    total_foreign_dec = agg.total_pretax
    dividend_foreign = float(total_foreign_dec / agg.shares)
    total_foreign = float(total_foreign_dec)
    total_jpy = int(
        (total_foreign_dec * rate_dec).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    return {
        "date": agg.date,
        "code": agg.code,
        "name": name,
        "dividend_foreign": dividend_foreign,
        "shares": shares_float,
        "total_foreign": total_foreign,
        "currency": currency,
        "exchange_rate": float(rate_dec),
        "total_jpy": total_jpy,
    }
