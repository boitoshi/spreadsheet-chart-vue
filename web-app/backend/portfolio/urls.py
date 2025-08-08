"""
ポートフォリオAPIのURLルーティング
Vue.jsダッシュボード連携用
"""
from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # 既存（レガシー）パス
    path('api/portfolio/', views.PortfolioAPIView.as_view(), name='portfolio-data'),
    path('api/portfolio/history/', views.PortfolioHistoryAPIView.as_view(), name='portfolio-history'),
    path('api/portfolio/stock/<str:stock_name>/', views.StockDetailAPIView.as_view(), name='stock-detail'),
    path('api/portfolio/validate/', views.DataValidationAPIView.as_view(), name='data-validation'),

    # 標準化（v1 用）パス
    path('portfolio/', views.PortfolioAPIView.as_view(), name='v1-portfolio-data'),
    path('portfolio/history/', views.PortfolioHistoryAPIView.as_view(), name='v1-portfolio-history'),
    path('portfolio/stock/<str:stock_name>/', views.StockDetailAPIView.as_view(), name='v1-stock-detail'),
    path('portfolio/validate/', views.DataValidationAPIView.as_view(), name='v1-data-validation'),
]
