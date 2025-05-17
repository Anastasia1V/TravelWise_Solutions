# airports/urls.py
from django.urls import path
from . import views

app_name = 'airports'  # Пространство имен для URL
urlpatterns = [
    path('api/search/', views.search_airports_api, name='search_airports_api'),
    path('add/<str:icao>/', views.add_airport, name='add_airport'),
    path('success/', views.success, name='success'),
]