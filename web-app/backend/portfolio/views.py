"""
ポートフォリオAPI views
Vue.jsダッシュボード連携用のRESTful API
"""
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
import json
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
            performance_data = sheets_service.get_latest_performance_data()
            
            if not portfolio_data:
                return JsonResponse({
                    'error': 'ポートフォリオデータが取得できませんでした',
                    'summary': {'totalValue': 0, 'totalProfit': 0, 'totalCost': 0},
                    'stocks': []
                }, status=200)
            
            # Vue.js形式に変換
            transformed_data = PortfolioDataTransformer.transform_to_vue_format(
                portfolio_data, performance_data
            )
            
            return JsonResponse(transformed_data, safe=False, json_dumps_params={'ensure_ascii': False})
            
        except Exception as e:
            return JsonResponse({
                'error': f'データ取得エラー: {str(e)}',
                'summary': {'totalValue': 0, 'totalProfit': 0, 'totalCost': 0},
                'stocks': []
            }, status=500)


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
            
            # Google Sheetsから履歴データ取得
            sheets_service = GoogleSheetsService()
            history_data = sheets_service.get_performance_history(period)
            
            if not history_data:
                return JsonResponse({
                    'periods': [],
                    'totalProfits': [],
                    'totalValues': [],
                    'message': '履歴データが見つかりませんでした'
                })
            
            # チャート用データ形式に変換
            chart_data = {
                'periods': [data['date'] for data in history_data],
                'totalProfits': [data['total_profit'] for data in history_data],
                'totalValues': [data['total_value'] for data in history_data],
                'totalCosts': [data['total_cost'] for data in history_data]
            }
            
            return JsonResponse(chart_data, safe=False, json_dumps_params={'ensure_ascii': False})
            
        except Exception as e:
            return JsonResponse({
                'error': f'履歴データ取得エラー: {str(e)}',
                'periods': [],
                'totalProfits': [],
                'totalValues': []
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StockDetailAPIView(View):
    """
    個別銘柄詳細API
    将来の機能拡張用
    """
    
    def get(self, request, stock_name):
        """指定銘柄の詳細情報を取得"""
        try:
            # Google Sheetsからデータ取得
            sheets_service = GoogleSheetsService()
            portfolio_data = sheets_service.get_portfolio_data()
            performance_data = sheets_service.get_latest_performance_data()
            
            # 指定銘柄のデータをフィルタリング
            stock_portfolio = [p for p in portfolio_data if p.get('銘柄名') == stock_name]
            stock_performance = [p for p in performance_data if p.get('銘柄名') == stock_name]
            
            if not stock_portfolio:
                return JsonResponse({
                    'error': f'銘柄「{stock_name}」が見つかりませんでした'
                }, status=404)
            
            # 個別銘柄用に変換
            transformed_data = PortfolioDataTransformer.transform_to_vue_format(
                stock_portfolio, stock_performance
            )
            
            # 最初の銘柄データのみ返す
            stock_detail = transformed_data['stocks'][0] if transformed_data['stocks'] else None
            
            return JsonResponse({
                'stock': stock_detail,
                'summary': transformed_data['summary']
            }, safe=False, json_dumps_params={'ensure_ascii': False})
            
        except Exception as e:
            return JsonResponse({
                'error': f'銘柄詳細取得エラー: {str(e)}'
            }, status=500)
