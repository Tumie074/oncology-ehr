from django.conf import settings
from django.db import models
from patients.models import Patient


class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        abstract = True
        ordering = ['-created_at']


class CamperCheckIn(Base):
    """Camper Medication Check-In and Assessment form."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='checkins')
    assessed_at = models.DateTimeField()
    physical_condition = models.TextField()
    medication_notes = models.TextField(blank=True, verbose_name='Medication (what the camper brought / is taking)')
    eyesight = models.CharField(max_length=120, blank=True)
    hearing = models.CharField(max_length=120, blank=True)
    mobility_aids = models.CharField(max_length=120, blank=True)
    prosthesis = models.CharField(max_length=120, blank=True)
    assist_bathing = models.BooleanField(default=False, verbose_name='Needs help showering / bathing')
    assist_dressing = models.BooleanField(default=False, verbose_name='Needs help dressing')
    assist_toileting = models.BooleanField(default=False, verbose_name='Needs help toileting')
    assist_eating = models.BooleanField(default=False, verbose_name='Needs help eating')
    tb_cough_2_weeks = models.BooleanField(default=False, verbose_name='TB screen: cough for more than 2 weeks')
    tb_weight_loss = models.BooleanField(default=False, verbose_name='TB screen: unexplained weight loss')
    tb_night_sweats = models.BooleanField(default=False, verbose_name='TB screen: night sweats or fevers')
    dietary_requirements = models.CharField(max_length=200, blank=True)
    additional_info = models.TextField(blank=True, verbose_name='Additional camper info (behavioural, psychosocial, self-care needs)')
    medical_person_name = models.CharField(max_length=150)
    medical_person_signature = models.TextField()

    def __str__(self):
        return f'Check-in {self.patient} {self.assessed_at:%Y-%m-%d}'


class MedShackVisit(Base):
    """Visit to MedShack record."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medshack_visits')
    visit_at = models.DateTimeField()
    organisation = models.CharField(max_length=150, blank=True, verbose_name='Organisation name')
    sex = models.CharField(max_length=10, blank=True)
    age = models.CharField(max_length=10, blank=True)
    accompanying = models.CharField(max_length=150, blank=True, verbose_name='Person accompanying')
    group = models.CharField(max_length=60, blank=True)
    reason = models.TextField(verbose_name='Reason for the visit')
    temperature = models.CharField(max_length=10, blank=True, verbose_name='Temperature (C)')
    pulse = models.CharField(max_length=10, blank=True, verbose_name='Pulse (bpm)')
    blood_pressure = models.CharField(max_length=20, blank=True)
    oxygen_saturation = models.CharField(max_length=10, blank=True, verbose_name='Oxygen saturation (%)')
    history = models.TextField(blank=True, verbose_name='Medical history')
    signs = models.TextField(blank=True, verbose_name='Signs and symptoms')
    findings = models.TextField(blank=True, verbose_name='Findings on examination')
    treatments = models.JSONField(default=list, blank=True)  # [{time, treatment, outcome}]
    advice1 = models.TextField(blank=True, verbose_name='Advice to crew member accompanying the camper (1)')
    advice2 = models.TextField(blank=True, verbose_name='Advice to crew member accompanying the camper (2)')
    nursing_report = models.TextField(blank=True)
    nurse_signature = models.TextField(verbose_name='Camp Nurse signature')
    doctor_signature = models.TextField(blank=True, verbose_name='Camp Doctor signature')

    def __str__(self):
        return f'MedShack {self.patient} {self.visit_at:%Y-%m-%d %H:%M}'


class NearMissReport(Base):
    """Medication / Treatment Event / Near Miss. Append-only: once filed it cannot be changed."""
    EVENT_TYPES = ['Extra Dose', 'Wrong Dose', 'Wrong Time', 'Wrong Camper', 'Omission', 'Omission of dose', 'Wrong drug', 'Expired product', 'Wrong treatment']
    FACTORS = ['Distractions', 'Workload', 'Cross Coverage']
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name='near_misses')
    camper_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    primary_dx = models.CharField(max_length=200, blank=True, verbose_name='Primary Dx')
    cabin = models.CharField(max_length=60, blank=True)
    event_at = models.DateTimeField(verbose_name='Date/time of event')
    discovered_at = models.DateTimeField(verbose_name='Date/time of discovery')
    description = models.TextField(verbose_name='Description of event')
    event_types = models.JSONField(default=list)
    initial_impression = models.TextField(blank=True)
    contributing_factors = models.JSONField(default=list, blank=True)
    immediate_action = models.TextField(blank=True, verbose_name='Immediate action taken')
    doctor_notified = models.TextField(blank=True, verbose_name='Notification of Camp Doctor')
    no_treatment_ordered = models.BooleanField(default=False)
    treatment_ordered = models.TextField(blank=True)
    reporter_name = models.CharField(max_length=150, verbose_name='Name of reporter')
    reporter_signature = models.TextField()
    investigation = models.TextField(blank=True, verbose_name='Event investigation and corrective action plan')
    medical_person = models.CharField(max_length=150, blank=True)
    medical_person_signature = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError('Near-miss reports cannot be edited once filed.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('Near-miss reports cannot be deleted.')

    def __str__(self):
        return f'Near miss {self.camper_name} {self.event_at:%Y-%m-%d}'


class CrewCheckIn(Base):
    """Medical Centre Check-In for staff / crew members (stored apart from camper records)."""
    name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    date = models.DateField()
    has_allergies = models.BooleanField(default=False, verbose_name='Allergies')
    allergies = models.CharField(max_length=300, blank=True, verbose_name='Which allergies?')
    medication = models.TextField(blank=True)
    broviac_portacath = models.BooleanField(default=False, verbose_name='Broviac / Port-a-cath')
    blood_count = models.CharField(max_length=60, blank=True)
    comments = models.TextField(blank=True, verbose_name='Other comments')
    medical_person_name = models.CharField(max_length=150)
    medical_person_signature = models.TextField()
    crew_signature = models.TextField(verbose_name='Camp crew signature')

    def __str__(self):
        return f'Crew check-in {self.name} {self.date}'


class CrewIndemnity(Base):
    """Camp Crew Member Indemnity and Media Release."""
    full_name = models.CharField(max_length=150, verbose_name='Full name and surname')
    id_number = models.CharField(max_length=30, verbose_name='ID number')
    camp_dates = models.CharField(max_length=100)
    camp_venue = models.CharField(max_length=150)
    signed_at_place = models.CharField(max_length=100, verbose_name='Signed at (place)')
    date = models.DateField()
    signature = models.TextField(verbose_name='Crew member signature')
    witness_name = models.CharField(max_length=150, verbose_name='Witness name and surname')
    witness_signature = models.TextField()

    class Meta(Base.Meta):
        verbose_name_plural = 'crew indemnities'

    def __str__(self):
        return f'Crew indemnity {self.full_name}'
