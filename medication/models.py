from datetime import timedelta
from django.db import models
from django.utils import timezone
from patients.models import Patient

class MedicationRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medication_records')
    medication_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField()
    administered_time = models.DateTimeField(null=True, blank=True)
    administered_by = models.CharField(max_length=100, blank=True)
    missed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        status = "MISSED" if self.missed else "Given"
        return f"{self.patient} — {self.medication_name} ({status})"

    def save(self, *args, **kwargs):
        if not self.administered_time and self.scheduled_time < timezone.now():
            self.missed = True
        super().save(*args, **kwargs)

    GRACE = timedelta(minutes=60)

    @classmethod
    def refresh_missed(cls):
        """Auto-flag every unadministered dose whose scheduled time has passed."""
        return cls.objects.filter(administered_time__isnull=True, missed=False,
                                  scheduled_time__lt=timezone.now()).update(missed=True)

    def administer(self, by):
        now = timezone.now()
        self.administered_time = now
        self.administered_by = by
        self.missed = now > self.scheduled_time + self.GRACE  # given late stays flagged
        self.save()

    @property
    def status(self):
        if self.administered_time:
            return 'Given late' if self.missed else 'Given'
        return 'Missed' if self.missed else 'Upcoming'
