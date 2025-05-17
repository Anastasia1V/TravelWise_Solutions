# airports/urls.py
from django.urls import path
from . import views

app_name = 'airports'  # Пространство имен для URL
urlpatterns = [
    path('api/search/', views.search_airports_api, name='search_airports_api'),
    path('find/', views.find_airport_in_db, name='find_airport'),
    path('found/<str:icao_code>/', views.success_airport_found, name='success_found'),
    path('success/', views.success, name='success'),
]