from django.urls import path
from .views import get_data, api_index
from .manual_updater import (
    update_stock_price,
    bulk_update_prices,
    save_monthly_data,
    get_update_history
)
from .report_generator import (
    generate_report,
    generate_blog_content,
    get_report_templates
)
from .currency_views import (
    get_portfolio_data,
    get_currency_rates,
    get_currency_portfolio_summary
)

urlpatterns = [
    # ルート（index）
    path('', api_index, name='api_index'),

    # 既存（レガシー）エンドポイント
    path('get_data/', get_data, name='get_data'),
    path('update_stock_price/', update_stock_price, name='update_stock_price'),
    path('api/manual_update/', update_stock_price, name='manual_update'),
    path('bulk_update_prices/', bulk_update_prices, name='bulk_update_prices'),
    path('save_monthly_data/', save_monthly_data, name='save_monthly_data'),
    path('get_update_history/', get_update_history, name='get_update_history'),
    path('generate_report/<str:month>/', generate_report, name='generate_report'),
    path('generate_blog_content/<str:month>/', generate_blog_content, name='generate_blog_content'),
    path('get_report_templates/', get_report_templates, name='get_report_templates'),
    path('portfolio/', get_portfolio_data, name='get_portfolio_data'),
    path('currency_rates/', get_currency_rates, name='get_currency_rates'),
    path('currency_summary/', get_currency_portfolio_summary, name='get_currency_portfolio_summary'),

    # 標準化（v1 用）エンドポイント
    path('data/records/', get_data, name='v1_get_data'),
    path('manual/update/', update_stock_price, name='v1_manual_update'),
    path('manual/bulk-update/', bulk_update_prices, name='v1_bulk_update'),
    path('monthly/save/', save_monthly_data, name='v1_save_monthly'),
    path('reports/generate/<str:month>/', generate_report, name='v1_generate_report'),
    path('reports/blog/<str:month>/', generate_blog_content, name='v1_generate_blog'),
    path('reports/templates/', get_report_templates, name='v1_report_templates'),
    path('currency/portfolio/', get_portfolio_data, name='v1_currency_portfolio'),
    path('currency/rates/', get_currency_rates, name='v1_currency_rates'),
    path('currency/summary/', get_currency_portfolio_summary, name='v1_currency_summary'),
]
