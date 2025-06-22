from django.urls import path
from .views import get_data
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

urlpatterns = [
    path('get_data/', get_data, name='get_data'),
    
    # 手動更新API
    path('update_stock_price/', update_stock_price, name='update_stock_price'),
    path('bulk_update_prices/', bulk_update_prices, name='bulk_update_prices'),
    path('save_monthly_data/', save_monthly_data, name='save_monthly_data'),
    path('get_update_history/', get_update_history, name='get_update_history'),
    
    # レポート生成API
    path('generate_report/<str:month>/', generate_report, name='generate_report'),
    path('generate_blog_content/<str:month>/', generate_blog_content, name='generate_blog_content'),
    path('get_report_templates/', get_report_templates, name='get_report_templates'),
]
