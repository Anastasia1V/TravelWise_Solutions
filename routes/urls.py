from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    path('my_routes/', views.my_routes,      name='my_routes'),
    path('create/',    views.create_route,   name='create_route'),
    path('view/<int:route_id>/', views.view_route, name='view_route'),
    path('edit/<int:route_id>/', views.edit_route, name='edit_route'),
    path('<path:unused>', views.home_redirect),
]
