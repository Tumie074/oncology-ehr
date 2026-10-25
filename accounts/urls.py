from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.CHRSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('unlock/', views.unlock, name='unlock'),
    path('audit/', views.audit_log, name='audit_log'),
]
