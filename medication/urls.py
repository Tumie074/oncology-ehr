from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule, name='medication_schedule'),
    path('add/<int:pk>/', views.add_medication, name='add_medication'),
    path('patient/<int:pk>/', views.weekly, name='patient_medlog'),
    path('<int:pk>/administer/', views.administer, name='administer'),
]
