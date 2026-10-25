from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'last_name', 'first_name', 'diagnosis', 'allergies')
    search_fields = ('case_number', 'first_name', 'last_name')
