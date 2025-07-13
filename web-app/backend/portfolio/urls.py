"""
ポートフォリオAPIのURLルーティング
Vue.jsダッシュボード連携用
"""
from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # メインポートフォリオデータAPI
    path('api/portfolio/', views.PortfolioAPIView.as_view(), name='portfolio-data'),
    
    # 損益推移履歴API
    path('api/portfolio/history/', views.PortfolioHistoryAPIView.as_view(), name='portfolio-history'),
    
    # 個別銘柄詳細API（将来拡張用）
    path('api/portfolio/stock/<str:stock_name>/', views.StockDetailAPIView.as_view(), name='stock-detail'),
]