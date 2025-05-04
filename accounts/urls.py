from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
    path('welcome/',  views.welcome_view,  name='welcome'),
    path('<path:unused>', views.home_redirect_view),
]
