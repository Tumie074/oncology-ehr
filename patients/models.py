from django.db import models

class Patient(models.Model):
    case_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    diagnosis = models.CharField(max_length=200)
    allergies = models.CharField(max_length=300, blank=True, help_text='Comma-separated, e.g. Penicillin, Latex')
    medical_notes = models.TextField(blank=True, help_text='Clinical precautions shown in the alert banner')
    guardian_name = models.CharField(max_length=150)
    guardian_contact = models.CharField(max_length=20)
    date_registered = models.DateField(auto_now_add=True)

    # --- Camper Registration and Indemnity form (extra fields) ---
    SEX = [('F', 'Female'), ('M', 'Male'), ('O', 'Other')]
    TB = [('', 'Select'), ('negative', 'Negative'), ('past', 'Past'), ('current', 'Current'), ('on-treatment', 'On treatment')]
    YESNO = [('', 'Select'), ('yes', 'Yes'), ('no', 'No')]
    sex = models.CharField(max_length=1, choices=[('', 'Select')] + SEX, blank=True)
    language = models.CharField(max_length=60, blank=True)
    religion = models.CharField(max_length=60, blank=True)
    tshirt_size = models.CharField(max_length=10, blank=True)
    address = models.TextField(blank=True)
    camp_session_date = models.DateField(null=True, blank=True)
    relationship_to_child = models.CharField(max_length=60, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_cell = models.CharField(max_length=20, blank=True)
    clinic_file_number = models.CharField(max_length=60, blank=True)
    clinic_contact_details = models.TextField(blank=True)
    current_medication = models.TextField(blank=True)
    medication_handed_in = models.CharField(max_length=3, choices=YESNO, blank=True)
    viral_load_over_1000 = models.CharField(max_length=3, choices=YESNO, blank=True)
    tb_history = models.CharField(max_length=20, choices=TB, blank=True)
    hepatitis_b = models.CharField(max_length=3, choices=YESNO, blank=True)
    adherence_barriers = models.TextField(blank=True)
    tb_cough_2_weeks = models.BooleanField(default=False, verbose_name='Cough for more than 2 weeks')
    tb_weight_loss = models.BooleanField(default=False, verbose_name='Unexplained weight loss')
    tb_night_sweats = models.BooleanField(default=False, verbose_name='Night sweats or fevers')
    eyesight = models.CharField(max_length=120, blank=True)
    hearing = models.CharField(max_length=120, blank=True)
    mobility_aids = models.CharField(max_length=120, blank=True)
    prosthesis = models.CharField(max_length=120, blank=True)
    assist_bathing = models.BooleanField(default=False, verbose_name='Needs help showering / bathing')
    assist_dressing = models.BooleanField(default=False, verbose_name='Needs help dressing')
    assist_toileting = models.BooleanField(default=False, verbose_name='Needs help toileting')
    assist_eating = models.BooleanField(default=False, verbose_name='Needs help eating')
    dietary_requirements = models.CharField(max_length=200, blank=True)
    behavioural_notes = models.TextField(blank=True, verbose_name='Behavioural / psychosocial / self-care needs')
    additional_disclosures = models.TextField(blank=True)
    linked_sibling = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    # Indemnity and consent (signed on the registration page)
    indemnity_signed = models.BooleanField(default=False)
    indemnity_guardian_signature = models.TextField(blank=True)
    indemnity_witness_name = models.CharField(max_length=150, blank=True)
    indemnity_witness_signature = models.TextField(blank=True)
    indemnity_signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def allergy_list(self):
        return [a.strip() for a in self.allergies.split(',') if a.strip()]

    @property
    def has_alerts(self):
        return bool(self.allergy_list or self.medical_notes)

    @property
    def tb_flags(self):
        return [l for l, v in [('Cough > 2 weeks', self.tb_cough_2_weeks), ('Weight loss', self.tb_weight_loss), ('Night sweats / fevers', self.tb_night_sweats)] if v]

    @property
    def assistance_needs(self):
        return [l for l, v in [('Bathing', self.assist_bathing), ('Dressing', self.assist_dressing), ('Toileting', self.assist_toileting), ('Eating', self.assist_eating)] if v]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.case_number})"
