from django.urls import path
from . import views

app_name = 'general'

urlpatterns = [
    path('', views.app_login, name='app_login'),
    path('logout/', views.app_logout, name='app_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
]