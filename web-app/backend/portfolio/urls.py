"""
ポートフォリオAPIのURLルーティング
Vue.jsダッシュボード連携用
"""

from django.urls import URLPattern, URLResolver, path
from django.views.generic.base import RedirectView

from . import views

app_name = 'portfolio'

urlpatterns: list[URLPattern | URLResolver] = [
    # レガシー -> v1 へリダイレクト（互換維持）
    path('api/portfolio/', RedirectView.as_view(pattern_name='portfolio:v1-portfolio-data', permanent=False)),
    path('api/portfolio/history/', RedirectView.as_view(pattern_name='portfolio:v1-portfolio-history', permanent=False)),
    path('api/portfolio/validate/', RedirectView.as_view(pattern_name='portfolio:v1-data-validation', permanent=False)),
    path('api/portfolio/stock/<str:stock_name>/', RedirectView.as_view(pattern_name='portfolio:v1-stock-detail', permanent=False)),

    # 標準化（v1 用）パス
    path('portfolio/', views.PortfolioAPIView.as_view(), name='v1-portfolio-data'),
    path('portfolio/history/', views.PortfolioHistoryAPIView.as_view(), name='v1-portfolio-history'),
    path('portfolio/stock/<str:stock_name>/', views.StockDetailAPIView.as_view(), name='v1-stock-detail'),
    path('portfolio/validate/', views.DataValidationAPIView.as_view(), name='v1-data-validation'),
]
