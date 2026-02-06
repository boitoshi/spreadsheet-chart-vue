
from django.urls import URLPattern, URLResolver, path
from django.views.generic.base import RedirectView

from .currency_views import (
    get_currency_portfolio_summary,
    get_currency_rates,
    get_portfolio_data,
)
from .manual_updater import (
    bulk_update_prices,
    save_monthly_data,
    update_stock_price,
)
from .report_generator import (
    generate_blog_content,
    generate_report,
    get_report_templates,
)
from .views import api_index, get_data

urlpatterns: list[URLPattern | URLResolver] = [
    # ルート（index）
    path('', api_index, name='api_index'),

    # レガシー -> v1 へリダイレクト
    path('get_data/', RedirectView.as_view(url='/api/v1/data/records/', permanent=False, query_string=True)),
    path('update_stock_price/', RedirectView.as_view(url='/api/v1/manual/update/', permanent=False, query_string=True)),
    path('api/manual_update/', RedirectView.as_view(url='/api/v1/manual/update/', permanent=False, query_string=True)),
    path('bulk_update_prices/', RedirectView.as_view(url='/api/v1/manual/bulk-update/', permanent=False, query_string=True)),
    path('save_monthly_data/', RedirectView.as_view(url='/api/v1/monthly/save/', permanent=False, query_string=True)),
    path('get_update_history/', RedirectView.as_view(url='/api/v1/get_update_history/', permanent=False, query_string=True)),
    path('generate_report/<str:month>/', RedirectView.as_view(url='/api/v1/reports/generate/%(month)s/', permanent=False, query_string=True)),
    path('generate_blog_content/<str:month>/', RedirectView.as_view(url='/api/v1/reports/blog/%(month)s/', permanent=False, query_string=True)),
    path('get_report_templates/', RedirectView.as_view(url='/api/v1/reports/templates/', permanent=False, query_string=True)),
    path('portfolio/', RedirectView.as_view(url='/api/v1/currency/portfolio/', permanent=False, query_string=True)),
    path('currency_rates/', RedirectView.as_view(url='/api/v1/currency/rates/', permanent=False, query_string=True)),
    path('currency_summary/', RedirectView.as_view(url='/api/v1/currency/summary/', permanent=False, query_string=True)),

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
