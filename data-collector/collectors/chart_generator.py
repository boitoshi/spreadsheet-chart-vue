"""ブログ用グラフデータ生成モジュール"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sheets_writer import SheetsDataWriter


class ChartDataGenerator:
    """ブログ用グラフデータ生成クラス"""

    def __init__(self, sheets_writer: SheetsDataWriter) -> None:
        """初期化

        Args:
            sheets_writer: SheetsDataWriterインスタンス
        """
        self.sheets_writer = sheets_writer

    def generate_monthly_chart_data(
        self, year: int, month: int, months: int = 6
    ) -> dict:
        """月別推移グラフデータを生成

        Args:
            year: 対象年
            month: 対象月
            months: 遡る月数（デフォルト6ヶ月）

        Returns:
            {
                "labels": ["2024-07", "2024-08", ...],
                "total_values": [1200000, 1250000, ...],
                "total_costs": [1000000, 1000000, ...],
                "holdings_data": {
                    "任天堂": [55000, 60000, ...],
                    "NVDA": [127500, 150000, ...],
                    # ...
                }
            }
        """
        try:
            # 損益レポートデータ取得
            perf_sheet = self.sheets_writer.spreadsheet.worksheet("損益レポート")
            perf_records = perf_sheet.get_all_records()

            # 対象期間の月リストを生成
            target_months = self._generate_target_months(year, month, months)

            labels = []
            total_values = []
            total_costs = []
            holdings_data = {}

            for target_year, target_month in target_months:
                target_date = f"{target_year}-{target_month:02d}-末"
                labels.append(f"{target_year}-{target_month:02d}")

                # 該当月のデータをフィルタリング
                month_data = [
                    r for r in perf_records if r.get("日付") == target_date
                ]

                # 重複除去
                month_data = self._remove_duplicates(month_data)

                # 合計値計算（データなしの月はNone）
                if month_data:
                    month_total_cost = sum(
                        r.get("取得額", 0) for r in month_data
                    )
                    month_total_value = sum(
                        r.get("評価額", 0) for r in month_data
                    )
                else:
                    month_total_cost = None
                    month_total_value = None

                total_costs.append(month_total_cost)
                total_values.append(month_total_value)

                # 各銘柄のデータを記録
                month_index = len(labels) - 1
                found_names = set()
                for record in month_data:
                    name = record.get("銘柄名", "")
                    value = record.get("評価額", 0)

                    if name not in holdings_data:
                        # 新規銘柄: 過去月分をNoneで埋める
                        holdings_data[name] = [None] * month_index

                    holdings_data[name].append(value)
                    found_names.add(name)

                # データがなかった既知銘柄にNoneを追加
                for name in holdings_data:
                    if name not in found_names:
                        holdings_data[name].append(None)

            return {
                "labels": labels,
                "total_values": total_values,
                "total_costs": total_costs,
                "holdings_data": holdings_data,
            }

        except Exception as e:
            print(f"⚠️ グラフデータ生成エラー: {e}")
            import traceback

            traceback.print_exc()
            return {
                "labels": [],
                "total_values": [],
                "total_costs": [],
                "holdings_data": {},
            }

    def _generate_target_months(
        self, year: int, month: int, months: int
    ) -> list[tuple[int, int]]:
        """対象期間の年月リストを生成

        Args:
            year: 終了年
            month: 終了月
            months: 遡る月数

        Returns:
            [(年, 月), ...] のリスト（古い順）
        """
        result = []
        current_year = year
        current_month = month

        for _ in range(months):
            result.insert(0, (current_year, current_month))

            # 前月へ
            current_month -= 1
            if current_month < 1:
                current_month = 12
                current_year -= 1

        return result

    def _remove_duplicates(self, records: list) -> list:
        """重複レコードを除去（最新の更新日時のもののみ残す）"""
        stock_records = {}

        for record in records:
            stock_code = record.get("銘柄コード", "")
            if not stock_code:
                continue

            update_time = record.get("更新日時", "")

            if stock_code not in stock_records or update_time > stock_records[
                stock_code
            ].get("更新日時", ""):
                stock_records[stock_code] = record

        return list(stock_records.values())
