"""yfinance + matplotlib による株価折れ線チャート生成モジュール。

取得日から報告月末までの終値推移を折れ線で描画する。
ヘッドレス環境（GCE 等）での実行を前提に Agg バックエンドを使用する。
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import matplotlib

# GUI を使わない（ヘッドレス環境対応）
matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import yfinance as yf  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# 日本語フォントの候補（システムに存在するものを順に試す）
_JP_FONT_CANDIDATES = [
    "Hiragino Sans",  # macOS
    "Hiragino Maru Gothic Pro",
    "Yu Gothic",  # Windows
    "Meiryo",
    "Noto Sans CJK JP",  # Linux (Noto CJK)
    "IPAexGothic",  # Linux (IPA)
]


def _select_jp_font() -> str | None:
    """システムに存在する日本語フォントを返す。なければ None。"""
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for candidate in _JP_FONT_CANDIDATES:
        if candidate in available:
            return candidate
    return None


class ChartGenerator:
    """取得日からの株価推移を折れ線で描画するクラス。"""

    FIGURE_SIZE = (10, 4.5)
    DPI = 120
    LINE_COLOR = "#2c7be5"

    def __init__(self) -> None:
        font = _select_jp_font()
        if font:
            plt.rcParams["font.family"] = font
        plt.rcParams["axes.unicode_minus"] = False

    def generate(
        self,
        symbol: str,
        name: str,
        start_date: str,
        end_date: str,
        out_path: str,
        currency: str = "JPY",
    ) -> str:
        """株価の折れ線チャートを生成して PNG で保存する。

        Args:
            symbol: 銘柄コード（例: 7974.T, NVDA）
            name: 銘柄名（例: 任天堂）
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD, inclusive)
            out_path: 保存先 PNG パス
            currency: 通貨コード（ラベル用）

        Returns:
            保存先の絶対パス

        Raises:
            RuntimeError: yfinance からデータが取得できなかった場合
        """
        # yfinance の end は排他なので +1 日する
        fetch_end = (
            datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        df = yf.download(
            symbol,
            start=start_date,
            end=fetch_end,
            progress=False,
            auto_adjust=False,
        )
        if df is None or df.empty:
            raise RuntimeError(
                f"株価データが取得できませんでした: "
                f"{symbol} {start_date}〜{end_date}"
            )

        # Close 列を取得（yfinance の MultiIndex 対応）
        if isinstance(df.columns, type(df.columns)) and ("Close", symbol) in df.columns:
            close = df[("Close", symbol)]
        else:
            close = df["Close"]

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)

        ax.plot(close.index, close.values, color=self.LINE_COLOR, linewidth=1.5)

        ax.set_title(
            f"{name}（{symbol}） {start_date} 〜 {end_date}",
            fontsize=13,
            pad=12,
        )
        ax.set_ylabel(f"株価（{currency}）", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.4)

        self._format_date_axis(ax, start_date, end_date)
        self._format_price_axis(ax, currency)

        fig.autofmt_xdate()
        fig.tight_layout()

        fig.savefig(out_path, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        return os.path.abspath(out_path)

    @staticmethod
    def _format_date_axis(ax, start_date: str, end_date: str) -> None:
        """期間の長さに応じて X 軸の日付フォーマットを切り替える。"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days

        if days <= 60:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        elif days <= 365:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m"))
        elif days <= 365 * 3:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m"))
        else:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    @staticmethod
    def _format_price_axis(ax, currency: str) -> None:
        """通貨に応じた Y 軸価格フォーマッタを設定する。"""
        if currency == "JPY":
            ax.yaxis.set_major_formatter(
                FuncFormatter(lambda x, _: f"{int(x):,}")
            )
        else:
            ax.yaxis.set_major_formatter(
                FuncFormatter(lambda x, _: f"{x:,.2f}")
            )
