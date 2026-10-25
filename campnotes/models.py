from django.db import models
from patients.models import Patient

class CampNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='camp_notes')
    date_recorded = models.DateField(auto_now_add=True)
    recorded_by = models.CharField(max_length=100)
    observation = models.TextField(help_text="Daily observation notes")
    incident_report = models.TextField(blank=True, help_text="Leave blank if no incident occurred")
    adherence_barrier_noted = models.BooleanField(default=False, help_text="Matches 'Adherence Barriers' field on the Medical Information form")

    def __str__(self):
        return f"{self.patient} — {self.date_recorded}"