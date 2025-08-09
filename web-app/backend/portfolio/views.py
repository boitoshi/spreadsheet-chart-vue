"""
ポートフォリオAPI views
Vue.jsダッシュボード連携用のRESTful API
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .services import GoogleSheetsService, PortfolioDataTransformer


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(cache_page(60 * 5), name='dispatch')  # 5分間キャッシュ
class PortfolioAPIView(View):
    """
    メインポートフォリオデータAPI
    Vue.jsダッシュボードのメイン表示用
    """

    def get(self, request):
        """ポートフォリオ全データを取得"""
        try:
            # Google Sheetsからデータ取得
            sheets_service = GoogleSheetsService()
            portfolio_data = sheets_service.get_portfolio_data()
            data_record_data = sheets_service.get_data_record_data()

            if not portfolio_data:
                return JsonResponse({
                    'error': 'ポートフォリオデータが取得できませんでした',
                    'summary': {'totalValue': 0, 'totalProfit': 0, 'totalCost': 0},
                    'stocks': []
                }, status=200)

            # ポートフォリオ + データ記録シートから損益を直接計算
            performance_data = sheets_service.calculate_portfolio_performance(
                portfolio_data, data_record_data
            )

            # 最新データのみ抽出（Vue.js表示用）
            latest_performance = self._get_latest_performance(performance_data)

            # Vue.js形式に変換
            transformed_data = PortfolioDataTransformer.transform_to_vue_format(
                portfolio_data, latest_performance
            )

            # データ品質検証を実行（警告レベルのみ含める）
            validation_result = sheets_service.validate_data_integrity(
                portfolio_data, data_record_data
            )

            # 検証結果をレスポンスに追加
            transformed_data['dataQuality'] = {
                'isValid': validation_result['is_valid'],
                'warnings': validation_result['warnings'],
                'hasErrors': len(validation_result['errors']) > 0,
                'summary': validation_result['summary']
            }

            return JsonResponse(transformed_data, safe=False, json_dumps_params={'ensure_ascii': False})

        except Exception as e:
            return JsonResponse({
                'error': f'データ取得エラー: {str(e)}',
                'summary': {'totalValue': 0, 'totalProfit': 0, 'totalCost': 0},
                'stocks': []
            }, status=500)

    def _get_latest_performance(self, performance_data: list[dict]) -> list[dict]:
        """最新の損益データのみを抽出"""
        if not performance_data:
            return []

        # 最新の日付を取得
        latest_date = max(record['日付'] for record in performance_data if record['日付'])

        # 最新日付のデータのみを返す
        latest_records = [r for r in performance_data if r['日付'] == latest_date]

        return latest_records


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(cache_page(60 * 10), name='dispatch')  # 10分間キャッシュ
class PortfolioHistoryAPIView(View):
    """
    ポートフォリオ損益推移履歴API
    Vue.jsのチャート表示用
    """

    def get(self, request):
        """期間指定で損益推移データを取得"""
        try:
            # クエリパラメータから期間を取得
            period = request.GET.get('period', 'all')  # 6months, 1year, all

            # Google Sheetsからデータ取得
            sheets_service = GoogleSheetsService()
            portfolio_data = sheets_service.get_portfolio_data()
            data_record_data = sheets_service.get_data_record_data()

            # ポートフォリオ + データ記録シートから損益を直接計算
            performance_data = sheets_service.calculate_portfolio_performance(
                portfolio_data, data_record_data
            )

            if not performance_data:
                return JsonResponse({
                    'periods': [],
                    'totalProfits': [],
                    'totalValues': [],
                    'totalCosts': [],
                    'avgPurchasePrices': [],
                    'message': '履歴データが見つかりませんでした'
                })

            # 月別に集計
            monthly_summary = self._aggregate_monthly_data(performance_data)

            # チャート用データ形式に変換（証券アプリスタイル）
            chart_data = {
                'periods': [data['date'] for data in monthly_summary],
                'totalProfits': [data['total_profit'] for data in monthly_summary],
                'totalValues': [data['total_value'] for data in monthly_summary],
                'totalCosts': [data['total_cost'] for data in monthly_summary],
                'cumulativeInvestments': [data['total_cost'] for data in monthly_summary],  # 累積投資額（証券アプリスタイル）
                'avgPurchasePrices': [data['avg_purchase_price'] for data in monthly_summary]  # 後方互換性のため残す
            }

            return JsonResponse(chart_data, safe=False, json_dumps_params={'ensure_ascii': False})

        except Exception as e:
            return JsonResponse({
                'error': f'履歴データ取得エラー: {str(e)}',
                'periods': [],
                'totalProfits': [],
                'totalValues': [],
                'totalCosts': [],
                'cumulativeInvestments': [],
                'avgPurchasePrices': []
            }, status=500)

    def _aggregate_monthly_data(self, performance_data: list[dict]) -> list[dict]:
        """月別データに集計（実際の累積取得額ベース）"""
        monthly_data = {}

        for record in performance_data:
            date_key = record['日付']

            if date_key not in monthly_data:
                monthly_data[date_key] = {
                    'date': date_key,
                    'total_profit': 0,
                    'total_value': 0,
                    'total_cost': 0,  # 実際の累積取得額
                    'total_quantity': 0
                }

            monthly_data[date_key]['total_profit'] += record['損益']
            monthly_data[date_key]['total_value'] += record['評価額']
            monthly_data[date_key]['total_cost'] += record['取得額']  # 実際に投資した金額の累計
            monthly_data[date_key]['total_quantity'] += record['保有株数']

        # 実際の平均取得価格を計算（実際の累積投資額 ÷ 累積保有株数）
        for data in monthly_data.values():
            if data['total_quantity'] > 0:
                data['avg_purchase_price'] = data['total_cost'] / data['total_quantity']
            else:
                data['avg_purchase_price'] = 0

        # 日付でソート
        return sorted(monthly_data.values(), key=lambda x: x['date'])


@method_decorator(csrf_exempt, name='dispatch')
class StockDetailAPIView(View):
    """
    個別銘柄詳細API
    指定銘柄の時系列データを取得（取得時期以降のみ）
    """

    def get(self, request, stock_name):
        """指定銘柄の詳細情報を取得"""
        try:
            # Google Sheetsからデータ取得
            sheets_service = GoogleSheetsService()
            portfolio_data = sheets_service.get_portfolio_data()
            data_record_data = sheets_service.get_data_record_data()

            # 指定銘柄のデータをフィルタリング
            stock_portfolio = [p for p in portfolio_data if p.get('銘柄名') == stock_name]

            if not stock_portfolio:
                return JsonResponse({
                    'error': f'銘柄「{stock_name}」が見つかりませんでした'
                }, status=404)

            # 全体の損益計算を実行
            performance_data = sheets_service.calculate_portfolio_performance(
                portfolio_data, data_record_data
            )

            # 指定銘柄の損益データのみ抽出
            stock_performance = [p for p in performance_data if p.get('銘柄名') == stock_name]

            # 最新の損益データを取得
            latest_performance = self._get_latest_performance([
                p for p in performance_data if p.get('銘柄名') == stock_name
            ])

            # 個別銘柄用に変換
            transformed_data = PortfolioDataTransformer.transform_to_vue_format(
                stock_portfolio, latest_performance
            )

            # 時系列データを準備（取得時期以降のみ）
            time_series_data = self._prepare_stock_time_series(stock_performance)

            # 最初の銘柄データのみ返す
            stock_detail = transformed_data['stocks'][0] if transformed_data['stocks'] else None

            return JsonResponse({
                'stock': stock_detail,
                'summary': transformed_data['summary'],
                'timeSeries': time_series_data
            }, safe=False, json_dumps_params={'ensure_ascii': False})

        except Exception as e:
            return JsonResponse({
                'error': f'銘柄詳細取得エラー: {str(e)}'
            }, status=500)

    def _prepare_stock_time_series(self, stock_performance: list[dict]) -> dict:
        """銘柄の時系列データを準備（取得時期以降のみ）"""
        if not stock_performance:
            return {
                'labels': [],
                'profits': [],
                'values': [],
                'acquisitionPrices': [],
                'acquisitionMarkers': []
            }

        # 日付順にソート
        sorted_performance = sorted(stock_performance, key=lambda x: x['日付'])

        labels = []
        profits = []
        values = []
        acquisition_prices = []
        acquisition_markers = []

        for record in sorted_performance:
            # 日付をラベル形式に変換（YYYY-MM-DD → YYYY/MM）
            date_str = record['日付']
            try:
                from datetime import datetime
                if '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                elif '/' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                else:
                    continue

                label = f"{date_obj.year}/{date_obj.month:02d}"

                labels.append(label)
                profits.append(record['損益'])
                values.append(record['評価額'])
                acquisition_prices.append(record['取得単価'] * record['保有株数'])

                # 取引回数が変化した場合は取得マーカーを追加
                acquisition_count = record.get('取引回数', 0)
                if len(acquisition_markers) == 0 or acquisition_count > len([m for m in acquisition_markers if m]):
                    acquisition_markers.append(f"取得 ({acquisition_count}回目)")
                else:
                    acquisition_markers.append('')

            except (ValueError, KeyError):
                continue

        return {
            'labels': labels,
            'profits': profits,
            'values': values,
            'acquisitionPrices': acquisition_prices,
            'acquisitionMarkers': acquisition_markers
        }

    def _get_latest_performance(self, performance_data: list[dict]) -> list[dict]:
        """最新の損益データのみを抽出"""
        if not performance_data:
            return []

        # 最新の日付を取得
        latest_date = max(record['日付'] for record in performance_data if record['日付'])

        # 最新日付のデータのみを返す
        latest_records = [r for r in performance_data if r['日付'] == latest_date]

        return latest_records


@method_decorator(csrf_exempt, name='dispatch')
class DataValidationAPIView(View):
    """
    データ品質検証API
    スプレッドシートデータの整合性と品質を検証
    """

    def get(self, request):
        """データ検証を実行して結果を返す"""
        try:
            # Google Sheetsからデータ取得
            sheets_service = GoogleSheetsService()
            portfolio_data = sheets_service.get_portfolio_data()
            data_record_data = sheets_service.get_data_record_data()

            # データ検証を実行
            validation_result = sheets_service.validate_data_integrity(
                portfolio_data, data_record_data
            )

            # レスポンスにHTTPステータスを反映
            status_code = 200 if validation_result['is_valid'] else 400

            return JsonResponse(validation_result, status=status_code,
                              json_dumps_params={'ensure_ascii': False})

        except Exception as e:
            return JsonResponse({
                'is_valid': False,
                'errors': [f'検証処理エラー: {str(e)}'],
                'warnings': [],
                'summary': {}
            }, status=500, json_dumps_params={'ensure_ascii': False})
