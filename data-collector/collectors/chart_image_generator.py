"""ブログ用グラフ画像生成モジュール"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sheets_writer import SheetsDataWriter

try:
    import matplotlib
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    matplotlib.use("Agg")  # GUIなしのバックエンドを使用

    # 日本語フォント設定
    try:
        import matplotlib.font_manager as fm

        # macOSの日本語フォント
        japanese_fonts = ["Hiragino Sans", "Hiragino Maru Gothic Pro", "Yu Gothic"]
        available_fonts = [f.name for f in fm.fontManager.ttflist]

        for font in japanese_fonts:
            if font in available_fonts:
                plt.rcParams["font.sans-serif"] = [font] + plt.rcParams[
                    "font.sans-serif"
                ]
                break
    except Exception:
        pass  # フォント設定に失敗しても続行

    plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の文字化け対策
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ChartImageGenerator:
    """ブログ用グラフ画像生成クラス"""

    def __init__(self, sheets_writer: SheetsDataWriter) -> None:
        """初期化

        Args:
            sheets_writer: SheetsDataWriterインスタンス
        """
        self.sheets_writer = sheets_writer

    def generate_stock_chart(
        self,
        symbol: str,
        name: str,
        purchase_date: str,
        output_path: str,
        months: int = 12,
    ) -> bool:
        """銘柄別の株価推移チャート画像を生成

        Args:
            symbol: 銘柄コード
            name: 銘柄名
            purchase_date: 取得日（YYYY-MM-DD形式）
            output_path: 出力ファイルパス
            months: 表示期間（月数）

        Returns:
            True: 成功, False: 失敗
        """
        if not MATPLOTLIB_AVAILABLE:
            print("⚠️ matplotlibがインストールされていません")
            return False

        try:
            import yfinance as yf

            # 取得日から現在までのデータを取得
            purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d")
            end_date = datetime.now()

            # yfinanceでデータ取得
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=purchase_dt, end=end_date)

            if hist.empty:
                print(f"⚠️ {name}の株価データが取得できませんでした")
                return False

            # グラフ作成
            fig, ax = plt.subplots(figsize=(12, 6))

            # 株価推移の折れ線グラフ
            ax.plot(
                hist.index,
                hist["Close"],
                linewidth=2,
                color="#1f77b4",
                label="株価",
            )

            # 取得日のマーカー
            purchase_price = hist.iloc[0]["Close"]
            ax.scatter(
                [purchase_dt],
                [purchase_price],
                color="red",
                s=100,
                zorder=5,
                label=f"取得日 ({purchase_date})",
            )

            # グリッド
            ax.grid(True, alpha=0.3, linestyle="--")

            # タイトルとラベル
            ax.set_title(f"{name} ({symbol}) - 株価推移", fontsize=16, pad=20)
            ax.set_xlabel("日付", fontsize=12)
            ax.set_ylabel("株価", fontsize=12)

            # 日付フォーマット
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)

            # 凡例
            ax.legend(loc="upper left", fontsize=10)

            # レイアウト調整
            plt.tight_layout()

            # 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()

            print(f"✅ チャート画像を生成しました: {output_path}")
            return True

        except Exception as e:
            print(f"❌ チャート生成エラー ({name}): {e}")
            import traceback

            traceback.print_exc()
            return False

    def generate_portfolio_chart(
        self, chart_data: dict, output_path: str, title: str = "ポートフォリオ推移"
    ) -> bool:
        """ポートフォリオ全体の推移チャート画像を生成

        Args:
            chart_data: グラフデータ（ChartDataGeneratorの出力）
            output_path: 出力ファイルパス
            title: グラフタイトル

        Returns:
            True: 成功, False: 失敗
        """
        if not MATPLOTLIB_AVAILABLE:
            print("⚠️ matplotlibがインストールされていません")
            return False

        try:
            labels = chart_data.get("labels", [])
            total_values = chart_data.get("total_values", [])
            total_costs = chart_data.get("total_costs", [])

            if not labels or not total_values:
                print("⚠️ グラフデータが不足しています")
                return False

            # グラフ作成
            fig, ax = plt.subplots(figsize=(12, 6))

            # 評価額の折れ線グラフ
            ax.plot(
                labels,
                total_values,
                linewidth=2.5,
                color="#2ca02c",
                marker="o",
                label="評価額",
            )

            # 取得額の折れ線グラフ
            ax.plot(
                labels,
                total_costs,
                linewidth=2,
                color="#ff7f0e",
                linestyle="--",
                marker="s",
                label="取得額",
            )

            # 損益がプラスかマイナスかで背景色を変える
            for i in range(len(labels)):
                if total_values[i] > total_costs[i]:
                    ax.axvspan(
                        i - 0.5, i + 0.5, alpha=0.1, color="green", zorder=0
                    )
                else:
                    ax.axvspan(i - 0.5, i + 0.5, alpha=0.1, color="red", zorder=0)

            # グリッド
            ax.grid(True, alpha=0.3, linestyle="--")

            # タイトルとラベル
            ax.set_title(title, fontsize=16, pad=20)
            ax.set_xlabel("月", fontsize=12)
            ax.set_ylabel("金額（円）", fontsize=12)

            # Y軸のフォーマット（カンマ区切り）
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f"{int(x):,}")
            )

            # X軸のラベル回転
            plt.xticks(rotation=45)

            # 凡例
            ax.legend(loc="upper left", fontsize=10)

            # レイアウト調整
            plt.tight_layout()

            # 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()

            print(f"✅ ポートフォリオチャート画像を生成しました: {output_path}")
            return True

        except Exception as e:
            print(f"❌ ポートフォリオチャート生成エラー: {e}")
            import traceback

            traceback.print_exc()
            return False

    def generate_all_charts(
        self, year: int, month: int, report_data: dict, chart_data: dict
    ) -> dict:
        """全銘柄のチャート画像とポートフォリオチャートを生成

        Args:
            year: 年
            month: 月
            report_data: レポートデータ
            chart_data: グラフデータ

        Returns:
            生成されたファイルパスの辞書
            {
                "portfolio": "path/to/portfolio.png",
                "stocks": {
                    "NVDA": "path/to/nvda.png",
                    ...
                }
            }
        """
        output_dir = os.path.join("output", f"{year}_{month:02d}_charts")
        os.makedirs(output_dir, exist_ok=True)

        result = {"portfolio": None, "stocks": {}}

        # ポートフォリオ全体のチャート
        portfolio_path = os.path.join(output_dir, "portfolio.png")
        if self.generate_portfolio_chart(
            chart_data, portfolio_path, title=f"{year}年{month}月 ポートフォリオ推移"
        ):
            result["portfolio"] = portfolio_path

        # 各銘柄のチャート
        try:
            portfolio_sheet = self.sheets_writer.spreadsheet.worksheet("ポートフォリオ")
            portfolio_records = portfolio_sheet.get_all_records()

            for holding in report_data.get("holdings", []):
                symbol = holding.get("symbol", "")
                name = holding.get("name", "")

                # ポートフォリオシートから取得日を取得
                portfolio_entry = next(
                    (p for p in portfolio_records if p.get("銘柄コード") == symbol),
                    {},
                )
                purchase_date = portfolio_entry.get("取得日", "")

                if not purchase_date:
                    print(f"⚠️ {name}の取得日が見つかりません")
                    continue

                # ファイル名を安全にする（記号を除去）
                safe_symbol = symbol.replace(".", "_").replace("/", "_")
                chart_path = os.path.join(output_dir, f"{safe_symbol}.png")

                if self.generate_stock_chart(
                    symbol, name, purchase_date, chart_path, months=12
                ):
                    result["stocks"][symbol] = chart_path

        except Exception as e:
            print(f"⚠️ 銘柄別チャート生成中にエラー: {e}")

        return result
