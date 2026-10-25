from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('register/', views.register_patient, name='register_patient'),
    path('import/', views.import_csv, name='import_csv'),
    path('sync/', views.forms_sync_view, name='forms_sync'),
    path('forms-webhook/', views.forms_webhook, name='forms_webhook'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:pk>/registered/', views.register_success, name='register_success'),
]
