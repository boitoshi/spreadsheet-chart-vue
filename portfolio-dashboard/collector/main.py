#!/usr/bin/env python3
"""
データ収集メインスクリプト（SQLite版）
月次株価データ取得・SQLite保存・ブログ生成を実行
"""

import os
import sys
import time
from datetime import datetime, timedelta

from collectors.benchmark_collector import BenchmarkCollector
from collectors.db_writer import DbWriter
from collectors.report_generator import BlogReportGenerator
from collectors.sheets_sync import SheetsSync
from collectors.stock_collector import StockDataCollector
from collectors.template_engine import MarkdownTemplateEngine
from config.settings import (
    AI_COMMENTS_ENABLED,
    CURRENCY_SETTINGS,
    DB_PATH,
    GOOGLE_APPLICATION_CREDENTIALS,
    SPREADSHEET_ID,
    WP_APP_PASSWORD,
    WP_PUBLISH_ENABLED,
    WP_URL,
    WP_USER,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


class PortfolioDataCollector:
    """ポートフォリオデータ収集メインクラス（SQLite版）"""

    def __init__(self) -> None:
        """初期化"""
        self.db_writer = DbWriter(DB_PATH)
        self.sheets_sync = SheetsSync(
            GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID, DB_PATH
        )
        self.stock_collector = StockDataCollector()
        self.benchmark_collector = BenchmarkCollector(self.db_writer)
        self.report_generator = BlogReportGenerator(self.db_writer)
        self.template_engine = MarkdownTemplateEngine(
            template_dir=os.path.join(os.path.dirname(__file__), "templates")
        )

        # オプショナル: AI コメント生成
        self.ai_comment = None
        if AI_COMMENTS_ENABLED:
            try:
                from collectors.ai_comment import AiCommentGenerator

                self.ai_comment = AiCommentGenerator()
                print("  AI コメント生成: 有効")
            except Exception as e:
                print(f"  AI コメント生成: 無効（{e}）")

        # オプショナル: WordPress 投稿
        self.wp_publisher = None
        if WP_PUBLISH_ENABLED and WP_URL:
            from collectors.wp_publisher import WpPublisher

            self.wp_publisher = WpPublisher(WP_URL, WP_USER, WP_APP_PASSWORD)
            print("  WordPress 投稿: 有効")

    def collect_and_publish(self, year: int, month: int) -> bool:
        """月次バッチ: データ収集 → ブログ生成

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        print(f"\n=== {year}年{month}月 月次バッチ開始 ===")

        # 1. Sheets からポートフォリオ同期
        print("\n[1/7] Sheets からポートフォリオ同期中...")
        synced = self.sheets_sync.sync_holdings()
        print(f"  同期完了: {synced}件")

        # 2. yfinance で株価取得 → SQLite 保存
        print("\n[2/7] 株価データ収集中...")
        success = self.collect_monthly_data(year, month)
        if not success:
            print("❌ 株価データ収集に失敗しました")
            return False

        # 3. ベンチマーク（日経225/S&P500）取得 → SQLite 保存
        print("\n[3/7] ベンチマーク収集中...")
        self.benchmark_collector.collect(year, month)

        # 4. チャート画像生成（Phase 3 では未実装）
        print("\n[4/7] チャート生成: スキップ（Phase 3 未実装）")

        # 5. ブログ下書き生成
        print("\n[5/7] ブログ下書き生成中...")
        report_data = self.report_generator.get_monthly_report_data(year, month)
        output_path = None
        if report_data:
            markdown_text = self.template_engine.render("blog_template.md", report_data)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, f"blog_draft_{year}_{month:02d}.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            print(f"  ブログ下書きを生成しました: {output_path}")
        else:
            print("  レポートデータが取得できませんでした")

        # 6. AI コメント生成（オプショナル）
        print("\n[6/7] AI コメント生成中...")
        if self.ai_comment and report_data:
            ai_comments = self.ai_comment.generate_all(report_data)
            report_data["ai_comments"] = ai_comments
            # AI コメント付きで再生成
            markdown = self.template_engine.render("blog_template.md", report_data)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            print("  AI コメント付きブログを再生成しました")
        else:
            print("  スキップ（AI コメント無効 or データなし）")

        # 7. WordPress 下書き投稿（オプショナル）
        print("\n[7/7] WordPress 投稿中...")
        if self.wp_publisher and output_path:
            try:
                post_url = self.wp_publisher.create_draft(
                    title=f"{year}年{month}月の投資成績",
                    markdown_content=open(output_path, encoding="utf-8").read(),
                )
                print(f"  投稿完了: {post_url}")
            except Exception as e:
                print(f"  WordPress 投稿エラー: {e}")
        else:
            print("  スキップ（WordPress 投稿無効）")

        print(f"\n=== {year}年{month}月 月次バッチ完了 ===")
        return True

    def collect_monthly_data(self, year: int, month: int) -> bool:
        """株価データ収集・SQLite保存

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        # ポートフォリオ情報取得（holdings テーブル）
        portfolio_data = self.db_writer.get_portfolio_data()
        if not portfolio_data:
            print(
                "❌ ポートフォリオデータが取得できませんでした"
                "（holdings テーブルが空？）"
            )
            return False

        # 月末日付を計算
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        last_day_str = last_day.strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        price_count = 0
        pnl_count = 0

        for holding in portfolio_data:
            code = holding.get("code", "")
            name = holding.get("name", "")
            shares_raw = holding.get("shares")

            # 必須フィールドが空の行はスキップ
            if not code or not name or not shares_raw:
                continue
            shares = int(float(str(shares_raw)))

            # 取得日を解析して保有期間を判定
            acquired_date_str = holding.get("acquired_date", "")
            is_owned_in_month = True  # デフォルト: 保有扱い（取得日が空の場合）
            if acquired_date_str:
                try:
                    acquired_date = datetime.strptime(
                        str(acquired_date_str), "%Y-%m-%d"
                    )
                    is_owned_in_month = (year, month) >= (
                        acquired_date.year,
                        acquired_date.month,
                    )
                except ValueError:
                    pass  # パース失敗時は保有扱い

            # 外貨情報の取得
            acquired_price_foreign = float(holding.get("acquired_price_foreign") or 0)
            acquired_exchange_rate = float(holding.get("acquired_exchange_rate") or 1.0)

            # 円建て取得単価: acquired_price_jpy → 空なら外貨×レート
            acquired_price_jpy_raw = holding.get("acquired_price_jpy")
            if acquired_price_jpy_raw:
                acquired_price_jpy = float(acquired_price_jpy_raw)
            else:
                acquired_price_jpy = acquired_price_foreign * acquired_exchange_rate

            # 外貨単価が空なら円建て値をフォールバック
            if not acquired_price_foreign:
                acquired_price_foreign = acquired_price_jpy

            print(f"  処理中: {name} ({code})")

            # 株価データ取得
            stock_data = self.stock_collector.get_stock_data(code, year, month)
            if stock_data is None:
                continue

            # メトリクス計算
            metrics = self.stock_collector.calculate_stock_metrics(
                stock_data,
                code,
                acquired_price_foreign,
                acquired_exchange_rate,
                shares,
            )
            if metrics is None:
                continue

            # monthly_prices に保存
            self.db_writer.save_monthly_price(
                {
                    "date": last_day_str,
                    "code": code,
                    "price_jpy": metrics["month_end_price"],
                    "high": metrics["highest_price"],
                    "low": metrics["lowest_price"],
                    "average": metrics["average_price"],
                    "change_rate": metrics["monthly_change"],
                    "avg_volume": metrics["average_volume"],
                    "created_at": now_str,
                }
            )
            price_count += 1

            # 為替レートも保存（外貨銘柄の場合）
            if CURRENCY_SETTINGS.get("update_rates_with_stocks", True):
                currency = metrics.get("currency", "JPY")
                if currency != "JPY" and metrics.get("current_exchange_rate"):
                    current_rate = float(metrics["current_exchange_rate"])
                    self._save_exchange_rate(
                        currency, current_rate, last_day_str, now_str
                    )

            # monthly_pnl に保存（保有期間のみ）
            if is_owned_in_month:
                self.db_writer.save_monthly_pnl(
                    {
                        "date": f"{year}-{month:02d}-末",
                        "code": code,
                        "name": name,
                        "acquired_price": acquired_price_jpy,
                        "current_price": metrics["month_end_price"],
                        "shares": shares,
                        "cost": metrics["purchase_amount"],
                        "value": metrics["current_amount"],
                        "profit": metrics["profit_loss"],
                        "profit_rate": metrics["profit_rate"],
                        "currency": metrics.get("currency", "JPY"),
                        "acquired_price_foreign": metrics["purchase_price_foreign"],
                        "current_price_foreign": metrics["month_end_price_foreign"],
                        "acquired_exchange_rate": metrics["purchase_exchange_rate"],
                        "current_exchange_rate": metrics["current_exchange_rate"],
                        "updated_at": now_str,
                    }
                )
                pnl_count += 1

                # 表示
                currency_info = ""
                if metrics.get("exchange_rate"):
                    currency_info = (
                        f" [{metrics['currency']}: {metrics['exchange_rate']:.2f}円]"
                    )
                    stock_pl = metrics.get("stock_profit_loss", 0)
                    fx_pl = metrics.get("fx_profit_loss", 0)
                    currency_info += (
                        f" (株価:{stock_pl:+,.0f}円 / 為替:{fx_pl:+,.0f}円)"
                    )
                print(
                    f"    {name}: {metrics['profit_loss']:+,.0f}円 "
                    f"({metrics['profit_rate']:+.1f}%){currency_info}"
                )
            else:
                print(f"    {name}: 市場データのみ記録（取得日: {acquired_date_str}）")

        print(f"\n  市場データ保存: {price_count}件 / 損益レポート保存: {pnl_count}件")

        # 日本株のみの場合は為替レート取得がスキップされているため、ここで取得
        self._update_all_currency_rates(last_day_str, now_str)

        return price_count > 0

    def _save_exchange_rate(
        self, currency: str, rate: float, date_str: str, now_str: str
    ) -> None:
        """為替レートを SQLite に保存"""
        pair = f"{currency}/JPY"
        self.db_writer.save_exchange_rate(
            {
                "date": date_str,
                "pair": pair,
                "rate": rate,
                "prev_rate": None,
                "change_rate": None,
                "high": None,
                "low": None,
                "updated_at": now_str,
            }
        )

    def _update_all_currency_rates(self, date_str: str, now_str: str) -> None:
        """全通貨の為替レートを取得・保存"""
        if not CURRENCY_SETTINGS.get("update_rates_with_stocks", True):
            return

        print("\n  為替レート取得中...")
        rates = self.stock_collector.currency_converter.get_all_current_rates()
        for currency, rate in rates.items():
            if rate:
                self._save_exchange_rate(currency, float(rate), date_str, now_str)
        print(f"  為替レート保存: {len(rates)}通貨")

    def sync_holdings_only(self) -> bool:
        """Sheets 同期のみ実行"""
        print("\n=== Sheets → SQLite 銘柄マスタ同期 ===")
        synced = self.sheets_sync.sync_holdings()
        print(f"同期完了: {synced}件")
        return True

    def collect_benchmark_only(self, year: int, month: int) -> bool:
        """ベンチマーク収集のみ実行"""
        print(f"\n=== {year}年{month}月 ベンチマーク収集 ===")
        self.benchmark_collector.collect(year, month)
        return True

    def generate_blog_draft(self, year: int, month: int) -> bool:
        """ブログ下書き生成

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        print(f"\n=== {year}年{month}月 ブログ下書き生成 ===")

        report_data = self.report_generator.get_monthly_report_data(year, month)
        if not report_data:
            print("❌ レポートデータが取得できませんでした")
            return False

        markdown = self.template_engine.render("blog_template.md", report_data)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"blog_draft_{year}_{month:02d}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"  ブログ下書きを生成しました: {output_path}")
        return True

    def collect_range_data(
        self,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
        auto_confirm: bool = False,
    ) -> dict:
        """期間範囲でのデータ収集

        Args:
            start_year: 開始年
            start_month: 開始月
            end_year: 終了年
            end_month: 終了月
            auto_confirm: 自動確認フラグ

        Returns:
            実行結果サマリー
        """
        print(
            f"\n=== 期間範囲データ収集: "
            f"{start_year}年{start_month}月 〜 {end_year}年{end_month}月 ==="
        )

        # 総月数計算
        total_months = 0
        ty, tm = start_year, start_month
        while (ty, tm) <= (end_year, end_month):
            total_months += 1
            tm += 1
            if tm > 12:
                tm = 1
                ty += 1

        print(f"実行予定: {total_months}ヶ月分")

        if not auto_confirm:
            confirm = input("\n実行しますか？ (y/n): ").strip().lower()
            if confirm != "y":
                print("実行をキャンセルしました")
                return {"status": "cancelled"}

        success_count = 0
        error_count = 0
        error_details: list[str] = []

        current_year, current_month = start_year, start_month
        current_count = 0

        while (current_year, current_month) <= (end_year, end_month):
            current_count += 1
            print(
                f"\n[{current_count}/{total_months}] "
                f"{current_year}年{current_month}月..."
            )

            try:
                success = self.collect_monthly_data(current_year, current_month)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_details.append(
                        f"{current_year}年{current_month}月: データ取得失敗"
                    )
            except Exception as e:
                error_count += 1
                error_details.append(f"{current_year}年{current_month}月: {e}")
                print(f"❌ エラー: {e}")

            # API制限回避（最後の月以外）
            if (current_year, current_month) < (end_year, end_month):
                print("  10秒待機中...")
                time.sleep(10)

            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        print(f"\n=== 完了: 成功 {success_count}/{total_months}件 ===")
        if error_details:
            print("エラー詳細:")
            for e in error_details:
                print(f"  - {e}")

        return {
            "status": "completed",
            "total_months": total_months,
            "success_count": success_count,
            "error_count": error_count,
            "error_details": error_details,
        }

    def run_interactive(self) -> None:
        """対話型メインメニュー"""
        print("=== ポートフォリオデータ収集システム（SQLite版）===")

        while True:
            try:
                print("\n=== メインメニュー ===")
                print("1. 月次データ収集（株価 + ベンチマーク + ブログ）")
                print("2. 期間範囲データ収集")
                print("3. Sheets → SQLite 銘柄マスタ同期")
                print("4. ベンチマークのみ収集")
                print("5. ブログ下書き生成のみ")
                print("0. 終了")

                choice = input("\n選択してください: ").strip()

                if choice == "0":
                    break

                elif choice == "1":
                    year = int(input("年を入力 (例: 2024): "))
                    month = int(input("月を入力 (1-12): "))
                    if not 1 <= month <= 12:
                        print("月は 1-12 の範囲で入力してください")
                        continue
                    self.collect_and_publish(year, month)

                elif choice == "2":
                    start_year = int(input("開始年 (例: 2024): "))
                    start_month = int(input("開始月 (1-12): "))
                    end_year = int(input("終了年 (例: 2025): "))
                    end_month = int(input("終了月 (1-12): "))
                    if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
                        print("月は 1-12 の範囲で入力してください")
                        continue
                    if (start_year, start_month) > (end_year, end_month):
                        print("開始年月は終了年月より前である必要があります")
                        continue
                    self.collect_range_data(
                        start_year, start_month, end_year, end_month
                    )

                elif choice == "3":
                    self.sync_holdings_only()

                elif choice == "4":
                    year = int(input("年を入力 (例: 2024): "))
                    month = int(input("月を入力 (1-12): "))
                    if not 1 <= month <= 12:
                        print("月は 1-12 の範囲で入力してください")
                        continue
                    self.collect_benchmark_only(year, month)

                elif choice == "5":
                    year = int(input("年を入力 (例: 2024): "))
                    month = int(input("月を入力 (1-12): "))
                    if not 1 <= month <= 12:
                        print("月は 1-12 の範囲で入力してください")
                        continue
                    self.generate_blog_draft(year, month)

                else:
                    print("❌ 無効な選択です")

            except ValueError:
                print("❌ 正しい数値を入力してください")
            except KeyboardInterrupt:
                print("\n終了します")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")


def _parse_year_month(args: list[str], flag: str) -> tuple[int, int] | None:
    """引数から年月を解析するヘルパー"""
    try:
        return int(args[0]), int(args[1])
    except (IndexError, ValueError):
        print("❌ 年と月は数値で指定してください")
        print(f"使用例: python main.py {flag} 2024 12")
        return None


def main() -> None:
    """メイン関数（CLI エントリーポイント）"""
    if not SPREADSHEET_ID:
        print("❌ SPREADSHEET_ID が設定されていません。.env ファイルを確認してください")
        return

    collector = PortfolioDataCollector()
    args = sys.argv[1:]

    # python main.py 2024 12  → バッチ（月次フル収集）
    if len(args) == 2 and args[0].isdigit():
        ym = _parse_year_month(args, "")
        if ym:
            print(f"バッチモード: {ym[0]}年{ym[1]}月")
            collector.collect_and_publish(*ym)

    # python main.py --sync  → Sheets同期のみ
    elif args == ["--sync"]:
        collector.sync_holdings_only()

    # python main.py --benchmark 2024 12  → ベンチマークのみ
    elif len(args) == 3 and args[0] == "--benchmark":
        ym = _parse_year_month(args[1:], "--benchmark")
        if ym:
            collector.collect_benchmark_only(*ym)

    # python main.py --blog 2024 12  → ブログ生成のみ
    elif len(args) == 3 and args[0] == "--blog":
        ym = _parse_year_month(args[1:], "--blog")
        if ym:
            collector.generate_blog_draft(*ym)

    # python main.py --range 2024 1 2024 12  → 期間範囲バッチ
    elif len(args) == 5 and args[0] == "--range":
        try:
            sy, sm, ey, em = int(args[1]), int(args[2]), int(args[3]), int(args[4])
            collector.collect_range_data(sy, sm, ey, em, auto_confirm=True)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py --range 2024 1 2024 12")

    # 引数なし  → 対話型
    elif not args:
        collector.run_interactive()

    else:
        print("使用方法:")
        print("  python main.py                         # 対話型")
        print("  python main.py 2024 12                 # 月次フル収集")
        print("  python main.py --sync                  # Sheets同期のみ")
        print("  python main.py --benchmark 2024 12     # ベンチマークのみ")
        print("  python main.py --blog 2024 12          # ブログ生成のみ")
        print("  python main.py --range 2024 1 2024 12  # 期間範囲バッチ")


if __name__ == "__main__":
    main()
