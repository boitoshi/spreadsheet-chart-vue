"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # 互換: 既存ルート（レガシー）
    path('', include('sheets.urls')),
    path('', include('portfolio.urls')),

    # 標準化: バージョン付きAPIプレフィックス
    # portfolio を先に含めることで /api/v1/portfolio/ を優先
    path('api/v1/', include('portfolio.urls')),
    path('api/v1/', include('sheets.urls')),
]
