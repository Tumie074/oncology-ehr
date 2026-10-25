from django.urls import path
from . import views

urlpatterns = [
    path('', views.hub, name='forms_hub'),
    path('<str:kind>/', views.form_list, name='form_list'),
    path('<str:kind>/new/', views.form_new, name='form_new'),
    path('<str:kind>/<int:pk>/', views.form_detail, name='form_detail'),
]
