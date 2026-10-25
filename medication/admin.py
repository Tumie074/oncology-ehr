from django.contrib import admin
from .models import MedicationRecord


@admin.register(MedicationRecord)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medication_name', 'dosage', 'scheduled_time', 'administered_time', 'missed')
    list_filter = ('missed',)
