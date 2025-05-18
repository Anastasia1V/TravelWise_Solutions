# core/urls.py
from django.urls import path
from . import views  # Импортируем views из текущего приложения core

app_name = 'core'

urlpatterns = [
    path('api/currencies/', views.get_available_currencies_api, name='available_currencies_api'),
    # Здесь могут быть другие URL вашего приложения core в будущем
]