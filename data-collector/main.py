#!/usr/bin/env python3
"""
データ収集メインスクリプト
月次株価データ取得とGoogle Sheets転記を実行
"""

import os
import sys
from datetime import datetime, timedelta

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), "collectors"))
sys.path.append(os.path.join(os.path.dirname(__file__), "config"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from chart_generator import ChartDataGenerator
from report_generator import BlogReportGenerator
from settings import CURRENCY_SETTINGS, GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID
from sheets_writer import SheetsDataWriter
from stock_collector import StockDataCollector
from template_engine import MarkdownTemplateEngine


class PortfolioDataCollector:
    """ポートフォリオデータ収集メインクラス"""

    def __init__(self) -> None:
        """初期化"""
        self.stock_collector = StockDataCollector()
        self.sheets_writer = SheetsDataWriter(
            GOOGLE_APPLICATION_CREDENTIALS, SPREADSHEET_ID
        )

    def collect_monthly_data(self, year: int, month: int) -> bool:
        """月次データ収集（全シート更新）

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        print(f"\n📊 {year}年{month}月のポートフォリオ分析を開始...")

        # Google Sheets設定
        if not self._setup_sheets():
            return False

        # 株価データ収集・計算
        stock_results = self._collect_stock_data(year, month)
        if not stock_results:
            print("❌ データの取得に失敗しました")
            return False

        data_record_results, performance_results, last_day = stock_results

        # 全シートに保存
        if data_record_results:
            self.sheets_writer.save_data_record(data_record_results)

        if performance_results:
            self.sheets_writer.save_performance_data(performance_results)

        # 為替レート取得・保存
        self._update_currency_rates(last_day)

        if performance_results:
            print(f"\n🎉 {year}年{month}月のデータ取得・分析が完了しました！")
            print("   Django backendからWebアプリで確認できます")
            self.sheets_writer.display_portfolio_summary(year, month)
            return True
        else:
            print("❌ データの取得に失敗しました")
            return False

    def _setup_sheets(self) -> bool:
        """Google Sheets接続・初期化"""
        if not self.sheets_writer.setup_google_sheets():
            print("❌ Google Sheets接続に失敗しました")
            return False

        # シート初期化
        self.sheets_writer.setup_portfolio_sheet()
        self.sheets_writer.setup_data_record_sheet()
        self.sheets_writer.setup_performance_sheet()
        self.sheets_writer.setup_currency_sheet()
        return True

    def _collect_stock_data(
        self, year: int, month: int
    ) -> tuple[list, list, datetime] | None:
        """株価データ収集・計算処理

        Args:
            year: 年
            month: 月

        Returns:
            (data_record_results, performance_results, last_day) または None
        """
        # ポートフォリオ情報取得
        portfolio_data = self.sheets_writer.get_portfolio_data()
        if not portfolio_data:
            print("❌ ポートフォリオデータが取得できませんでした")
            return None

        data_record_results = []
        performance_results = []

        # 月末日付を計算
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        # 各銘柄のデータ収集
        for holding in portfolio_data:
            symbol = holding["銘柄コード"]
            name = holding["銘柄名"]
            purchase_price = float(holding["取得単価（円）"])
            shares = int(holding["保有株数"])

            print(f"  📈 {name} ({symbol}) を処理中...")

            # 株価データ取得
            stock_data = self.stock_collector.get_stock_data(symbol, year, month)
            if stock_data is None:
                continue

            # メトリクス計算
            metrics = self.stock_collector.calculate_stock_metrics(
                stock_data, symbol, purchase_price, shares
            )
            if metrics is None:
                continue

            # 市場データ専用のデータ記録形式（保有情報を除外）
            data_record_results.append(
                [
                    last_day.strftime("%Y-%m-%d"),  # 月末日付
                    symbol,  # 銘柄コード
                    metrics["month_end_price"],  # 月末価格（円）
                    metrics["highest_price"],  # 最高値
                    metrics["lowest_price"],  # 最安値
                    metrics["average_price"],  # 平均価格
                    metrics["monthly_change"],  # 月間変動率(%)
                    metrics["average_volume"],  # 平均出来高
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 取得日時
                ]
            )

            # 損益レポート用データ準備
            performance_results.append(
                [
                    f"{year}-{month:02d}-末",
                    symbol,
                    name,
                    purchase_price,
                    metrics["month_end_price"],
                    shares,
                    metrics["purchase_amount"],
                    metrics["current_amount"],
                    metrics["profit_loss"],
                    metrics["profit_rate"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

            # 外貨情報の表示
            currency_info = ""
            if metrics.get("exchange_rate"):
                currency_info = (
                    f" [{metrics['currency']}: {metrics['exchange_rate']:.2f}円]"
                )

            print(
                f"    ✅ {name}: {metrics['profit_loss']:+,.0f}円 "
                f"({metrics['profit_rate']:+.1f}%){currency_info}"
            )

        return data_record_results, performance_results, last_day

    def _update_currency_rates(self, date: datetime | None = None) -> None:
        """為替レート更新"""
        if not CURRENCY_SETTINGS.get("update_rates_with_stocks", True):
            return

        print("\n💱 為替レート取得中...")
        exchange_rates = self.stock_collector.currency_converter.get_all_current_rates()
        print(f"✅ {len(exchange_rates)}通貨の為替レート取得完了")

        if exchange_rates:
            target_date = date if date else datetime.now()
            self.sheets_writer.save_currency_rates(exchange_rates, target_date)

    def update_currency_rates_only(self, date: datetime | None = None) -> bool:
        """為替レートのみ更新

        Args:
            date: 更新日付（デフォルトは現在日時）

        Returns:
            成功/失敗
        """
        print("\n💱 === 為替レート更新開始 ===")

        # Google Sheets設定
        if not self.sheets_writer.setup_google_sheets():
            print("❌ Google Sheets接続に失敗しました")
            return False

        self.sheets_writer.setup_currency_sheet()

        # 為替レート取得・保存
        self._update_currency_rates(date)

        print("🎉 為替レートの更新が完了しました！")
        return True

    def update_market_data_only(self, year: int, month: int) -> bool:
        """市場データ（データ記録）のみ更新

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        print(f"\n📈 === {year}年{month}月 市場データ更新開始 ===")

        # Google Sheets設定
        if not self._setup_sheets():
            return False

        # 株価データ収集・計算
        stock_results = self._collect_stock_data(year, month)
        if not stock_results:
            print("❌ 市場データの取得に失敗しました")
            return False

        data_record_results, _, _ = stock_results

        # データ記録シートのみ保存
        if data_record_results:
            self.sheets_writer.save_data_record(data_record_results)
            print(f"🎉 {year}年{month}月の市場データ更新が完了しました！")
            return True
        else:
            print("❌ 市場データの保存に失敗しました")
            return False

    def update_performance_only(self, year: int, month: int) -> bool:
        """損益レポートのみ更新

        Args:
            year: 年
            month: 月

        Returns:
            成功/失敗
        """
        print(f"\n📊 === {year}年{month}月 損益レポート更新開始 ===")

        # Google Sheets設定
        if not self._setup_sheets():
            return False

        # 株価データ収集・計算
        stock_results = self._collect_stock_data(year, month)
        if not stock_results:
            print("❌ 損益データの計算に失敗しました")
            return False

        _, performance_results, _ = stock_results

        # 損益レポートシートのみ保存
        if performance_results:
            self.sheets_writer.save_performance_data(performance_results)
            print(f"🎉 {year}年{month}月の損益レポート更新が完了しました！")
            self.sheets_writer.display_portfolio_summary(year, month)
            return True
        else:
            print("❌ 損益レポートの保存に失敗しました")
            return False

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
            auto_confirm: 自動確認フラグ（非対話型実行用）

        Returns:
            実行結果サマリー
        """
        print("\n📊 === 期間範囲データ収集開始 ===")
        print(
            f"🎯 対象期間: {start_year}年{start_month}月 〜 {end_year}年{end_month}月"
        )

        # 実行統計
        success_count = 0
        error_count = 0
        error_details = []

        # 月ごとのループ実行
        current_year, current_month = start_year, start_month
        total_months = 0

        # 総月数計算
        temp_year, temp_month = start_year, start_month
        while (temp_year, temp_month) <= (end_year, end_month):
            total_months += 1
            temp_month += 1
            if temp_month > 12:
                temp_month = 1
                temp_year += 1

        print(f"📅 実行予定: {total_months}ヶ月分のデータ収集")

        # 実行確認
        if not auto_confirm:
            confirm = input("\n実行しますか？ (y/n): ").strip().lower()
            if confirm != "y":
                print("❌ 実行をキャンセルしました")
                return {"status": "cancelled"}
        else:
            print("\n🚀 自動実行モード: データ収集を開始します...")

        if not auto_confirm:
            print("\n🚀 データ収集を開始します...")

        # 各月のデータ収集実行
        current_count = 0
        while (current_year, current_month) <= (end_year, end_month):
            current_count += 1
            print(
                f"\n📊 [{current_count}/{total_months}] "
                f"{current_year}年{current_month}月のデータ収集中..."
            )

            try:
                success = self.collect_monthly_data(current_year, current_month)
                if success:
                    success_count += 1
                    print(f"✅ {current_year}年{current_month}月: 成功")
                else:
                    error_count += 1
                    error_details.append(
                        f"{current_year}年{current_month}月: データ取得失敗"
                    )
                    print(f"❌ {current_year}年{current_month}月: データ取得失敗")
            except Exception as e:
                error_count += 1
                error_details.append(
                    f"{current_year}年{current_month}月: 例外エラー - {str(e)}"
                )
                print(f"❌ {current_year}年{current_month}月: 例外エラー - {str(e)}")

            # 進捗表示
            progress = (current_count / total_months) * 100
            print(f"📈 進捗: {progress:.1f}% ({current_count}/{total_months})")

            # API制限回避のための待機（最後の月以外）
            if (current_year, current_month) < (end_year, end_month):
                print("⏳ API制限回避のため10秒待機...")
                import time

                time.sleep(10)

            # 次の月へ
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        # 実行結果サマリー
        print("\n🎉 === 期間範囲データ収集完了 ===")
        print("📊 実行結果:")
        print(f"  ✅ 成功: {success_count}件")
        print(f"  ❌ エラー: {error_count}件")
        print(f"  📈 成功率: {(success_count / total_months * 100):.1f}%")

        if error_details:
            print("\n⚠️ エラー詳細:")
            for error in error_details:
                print(f"  - {error}")

        return {
            "status": "completed",
            "total_months": total_months,
            "success_count": success_count,
            "error_count": error_count,
            "error_details": error_details,
        }

    def generate_blog_draft(self, year: int, month: int) -> None:
        """ブログ記事下書きを生成

        Args:
            year: 年
            month: 月
        """
        print(f"\n📝 === {year}年{month}月 ブログ記事下書き生成 ===")

        # Google Sheets設定
        if not self.sheets_writer.setup_google_sheets():
            print("❌ Google Sheets接続に失敗しました")
            return

        # レポートデータ取得
        report_gen = BlogReportGenerator(self.sheets_writer)
        report_data = report_gen.get_monthly_report_data(year, month)

        if not report_data:
            print("❌ レポートデータが取得できませんでした")
            return

        # グラフデータ生成（オプション）
        chart_gen = ChartDataGenerator(self.sheets_writer)
        chart_data = chart_gen.generate_monthly_chart_data(year, month, months=6)
        report_data["chart_data"] = chart_data

        # Markdown生成
        template_engine = MarkdownTemplateEngine()
        markdown = template_engine.render("blog_template.md", report_data)

        # ファイル保存
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"blog_draft_{year}_{month:02d}.md")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"✅ ブログ記事下書きを生成しました: {output_path}")
        print("   WordPressにコピー&ペーストしてご利用ください")

        # プレビュー表示
        preview_lines = markdown.split("\n")[:20]
        print("\n📄 プレビュー（最初の20行）:")
        print("=" * 60)
        print("\n".join(preview_lines))
        print("..." if len(markdown.split("\n")) > 20 else "")
        print("=" * 60)

    def run_interactive(self) -> None:
        """対話型実行"""
        print("=== 📊 ポートフォリオデータ収集システム ===")
        print("🎯 Django backend連携対応版")

        while True:
            try:
                print("\n=== メインメニュー ===")
                print("1. 月次データ取得・分析（全シート更新）")
                print("2. 期間範囲データ取得・分析（全シート更新）")
                print("3. 特定シート更新")
                print("4. ポートフォリオサマリー表示")
                print("5. シート初期化")
                print("6. 現在の為替レート表示")
                print("7. 📝 ブログ記事下書き生成")
                print("0. 終了")

                choice = input("\n選択してください: ").strip()

                if choice == "0":
                    break
                elif choice == "1":
                    # 月次データ取得
                    year = int(input("年を入力してください (例: 2024): "))
                    month = int(input("月を入力してください (1-12): "))

                    if month < 1 or month > 12:
                        print("月は1-12の範囲で入力してください。")
                        continue

                    self.collect_monthly_data(year, month)

                elif choice == "2":
                    # 期間範囲データ取得・分析
                    print("\n📊 期間範囲データ取得・分析")
                    start_year = int(input("開始年を入力してください (例: 2023): "))
                    start_month = int(input("開始月を入力してください (1-12): "))
                    end_year = int(input("終了年を入力してください (例: 2025): "))
                    end_month = int(input("終了月を入力してください (1-12): "))

                    # 入力値検証
                    if (
                        start_month < 1
                        or start_month > 12
                        or end_month < 1
                        or end_month > 12
                    ):
                        print("月は1-12の範囲で入力してください。")
                        continue

                    if (start_year, start_month) > (end_year, end_month):
                        print("開始年月は終了年月より前である必要があります。")
                        continue

                    # 期間範囲実行
                    self.collect_range_data(
                        start_year, start_month, end_year, end_month
                    )

                elif choice == "3":
                    # 特定シート更新
                    print("\n=== 特定シート更新メニュー ===")
                    print("3-1. 為替レートのみ更新")
                    print("3-2. 市場データのみ更新")
                    print("3-3. 損益レポートのみ更新")
                    print("0. メインメニューに戻る")

                    sub_choice = input("\n選択してください: ").strip()

                    if sub_choice == "0":
                        continue
                    elif sub_choice == "3-1" or sub_choice == "1":
                        # 為替レートのみ更新
                        self.update_currency_rates_only()
                    elif sub_choice == "3-2" or sub_choice == "2":
                        # 市場データのみ更新
                        year = int(input("年を入力してください (例: 2024): "))
                        month = int(input("月を入力してください (1-12): "))

                        if month < 1 or month > 12:
                            print("月は1-12の範囲で入力してください。")
                            continue

                        self.update_market_data_only(year, month)
                    elif sub_choice == "3-3" or sub_choice == "3":
                        # 損益レポートのみ更新
                        year = int(input("年を入力してください (例: 2024): "))
                        month = int(input("月を入力してください (1-12): "))

                        if month < 1 or month > 12:
                            print("月は1-12の範囲で入力してください。")
                            continue

                        self.update_performance_only(year, month)
                    else:
                        print("❌ 無効な選択です")

                elif choice == "4":
                    # サマリー表示
                    if not self.sheets_writer.setup_google_sheets():
                        print("❌ Google Sheets接続に失敗しました")
                        continue

                    year = int(input("表示する年を入力 (例: 2024): "))
                    month = int(input("表示する月を入力 (1-12): "))
                    self.sheets_writer.display_portfolio_summary(year, month)

                elif choice == "5":
                    # シート初期化
                    if not self.sheets_writer.setup_google_sheets():
                        print("❌ Google Sheets接続に失敗しました")
                        continue

                    confirm = input("⚠️ 全シートを初期化しますか？ (yes/no): ")
                    if confirm.lower() == "yes":
                        self.sheets_writer.setup_portfolio_sheet()
                        self.sheets_writer.setup_data_record_sheet()
                        self.sheets_writer.setup_performance_sheet()
                        self.sheets_writer.setup_currency_sheet()
                        print("✅ シートの初期化が完了しました")

                elif choice == "6":
                    # 為替レート表示
                    print("\n💱 現在の為替レート取得中...")
                    currency_converter = self.stock_collector.currency_converter
                    rates = currency_converter.display_current_rates()

                    # 為替レートをシートに保存するか確認
                    save_to_sheet = (
                        input("\n为替レートをスプレッドシートに保存しますか？ (y/n): ")
                        .strip()
                        .lower()
                    )
                    if save_to_sheet == "y":
                        if not self.sheets_writer.setup_google_sheets():
                            print("❌ Google Sheets接続に失敗しました")
                            continue

                        self.sheets_writer.setup_currency_sheet()
                        self.sheets_writer.save_currency_rates(rates, datetime.now())
                        print("✅ 為替レートをスプレッドシートに保存しました")

                elif choice == "7":
                    # ブログ記事下書き生成
                    year = int(input("年を入力してください (例: 2024): "))
                    month = int(input("月を入力してください (1-12): "))

                    if month < 1 or month > 12:
                        print("月は1-12の範囲で入力してください。")
                        continue

                    self.generate_blog_draft(year, month)

                else:
                    print("❌ 無効な選択です")

            except ValueError:
                print("❌ 正しい数値を入力してください")
            except KeyboardInterrupt:
                print("\nアプリを終了します")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")


def main() -> None:
    """メイン関数"""
    if not SPREADSHEET_ID:
        print("❌ SPREADSHEET_IDが設定されていません。.envファイルを確認してください。")
        print("   例: SPREADSHEET_ID=your_spreadsheet_id_here")
        return

    print(f"📋 スプレッドシートID: {SPREADSHEET_ID}")
    print(f"🔑 認証ファイル: {GOOGLE_APPLICATION_CREDENTIALS}")

    collector = PortfolioDataCollector()

    # コマンドライン引数でバッチ実行も可能
    if len(sys.argv) == 3:
        try:
            year = int(sys.argv[1])
            month = int(sys.argv[2])
            print(f"バッチモード: {year}年{month}月のデータを収集します")
            collector.collect_monthly_data(year, month)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py 2024 12")
    elif len(sys.argv) == 6 and sys.argv[1] == "--range":
        try:
            start_year = int(sys.argv[2])
            start_month = int(sys.argv[3])
            end_year = int(sys.argv[4])
            end_month = int(sys.argv[5])
            print(
                f"期間範囲モード: {start_year}年{start_month}月〜"
                f"{end_year}年{end_month}月のデータを収集します"
            )
            collector.collect_range_data(
                start_year, start_month, end_year, end_month, auto_confirm=True
            )
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py --range 2023 6 2025 6")
    elif len(sys.argv) == 2 and sys.argv[1] == "--currency-only":
        # 為替レートのみ更新
        print("為替レート更新モード")
        collector.update_currency_rates_only()
    elif len(sys.argv) == 4 and sys.argv[1] == "--market-data":
        try:
            year = int(sys.argv[2])
            month = int(sys.argv[3])
            print(f"市場データ更新モード: {year}年{month}月")
            collector.update_market_data_only(year, month)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py --market-data 2024 12")
    elif len(sys.argv) == 4 and sys.argv[1] == "--performance":
        try:
            year = int(sys.argv[2])
            month = int(sys.argv[3])
            print(f"損益レポート更新モード: {year}年{month}月")
            collector.update_performance_only(year, month)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py --performance 2024 12")
    elif len(sys.argv) == 4 and sys.argv[1] == "--blog":
        try:
            year = int(sys.argv[2])
            month = int(sys.argv[3])
            print(f"ブログ記事生成モード: {year}年{month}月")
            collector.generate_blog_draft(year, month)
        except ValueError:
            print("❌ 年と月は数値で指定してください")
            print("使用例: python main.py --blog 2024 12")
    else:
        # 対話型実行
        collector.run_interactive()


if __name__ == "__main__":
    main()
