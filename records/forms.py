from django import forms
from django.utils import timezone
from patients.forms import SectionedForm, SignatureField, style_fields
from .models import CamperCheckIn, CrewCheckIn, CrewIndemnity, MedShackVisit, NearMissReport

DT = '%Y-%m-%dT%H:%M'


def dt_field(label, required=True):
    return forms.DateTimeField(label=label, required=required, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format=DT),
                               input_formats=[DT, '%Y-%m-%d %H:%M'], initial=lambda: timezone.localtime().strftime(DT))


class RecordForm(SectionedForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        for f in self.fields.values():
            if isinstance(f.widget, forms.Textarea):
                f.widget.attrs.setdefault('rows', 3)


class CamperCheckInForm(RecordForm):
    assessed_at = dt_field('Date and time of assessment')
    medical_person_signature = SignatureField(label='Medical person sign-off (required)')
    sections = [
        ('Camper', ['patient', 'assessed_at']),
        ('Current physical condition and medication', ['physical_condition', 'medication_notes']),
        ('Accessibility', ['eyesight', 'hearing', 'mobility_aids', 'prosthesis']),
        ('Assistance with daily living and TB screening', ['assist_bathing', 'assist_dressing', 'assist_toileting', 'assist_eating', 'tb_cough_2_weeks', 'tb_weight_loss', 'tb_night_sweats']),
        ('Additional information', ['dietary_requirements', 'additional_info']),
        ('Medical person sign-off', ['medical_person_name', 'medical_person_signature']),
    ]

    class Meta:
        model = CamperCheckIn
        exclude = ['created_at', 'created_by']


class MedShackVisitForm(RecordForm):
    visit_at = dt_field('Date and time')
    nurse_signature = SignatureField(label='Camp Nurse signature')
    doctor_signature = SignatureField(label='Camp Doctor signature', required=False)
    sections = [
        ('Visit', ['patient', 'visit_at', 'organisation', 'sex', 'age', 'accompanying', 'group', 'reason']),
        ('Vital signs', ['temperature', 'pulse', 'blood_pressure', 'oxygen_saturation']),
        ('Assessment', ['history', 'signs', 'findings']),
        ('Advice and nursing report', ['advice1', 'advice2', 'nursing_report']),
        ('Signatures', ['nurse_signature', 'doctor_signature']),
    ]

    class Meta:
        model = MedShackVisit
        exclude = ['created_at', 'created_by', 'treatments']


class NearMissForm(RecordForm):
    event_at = dt_field('Date/time of event')
    discovered_at = dt_field('Date/time of discovery')
    event_types = forms.MultipleChoiceField(choices=[(x, x) for x in NearMissReport.EVENT_TYPES], widget=forms.CheckboxSelectMultiple,
                                            label='Type of event', error_messages={'required': 'Select at least one type of event.'})
    contributing_factors = forms.MultipleChoiceField(choices=[(x, x) for x in NearMissReport.FACTORS], widget=forms.CheckboxSelectMultiple,
                                                     required=False, label='Contributing factors')
    reporter_signature = SignatureField(label='Reporter signature')
    medical_person_signature = SignatureField(label='Medical person signature', required=False)
    sections = [
        ('Camper', ['patient', 'camper_name', 'date_of_birth', 'primary_dx', 'cabin']),
        ('Event', ['event_at', 'discovered_at', 'description', 'event_types', 'initial_impression', 'contributing_factors']),
        ('Response', ['immediate_action', 'doctor_notified', 'no_treatment_ordered', 'treatment_ordered']),
        ('Reporter', ['reporter_name', 'reporter_signature']),
        ('Investigation and corrective action plan', ['investigation', 'medical_person', 'medical_person_signature']),
    ]

    class Meta:
        model = NearMissReport
        exclude = ['created_at', 'created_by']
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].required = False
        self.fields['patient'].help_text = 'Optional: choose to link this report to a camper record.'
        self.fields['camper_name'].required = False

    def clean(self):
        data = super().clean()
        p = data.get('patient')
        if p:
            data['camper_name'] = data.get('camper_name') or p.full_name
            data['date_of_birth'] = data.get('date_of_birth') or p.date_of_birth
            data['primary_dx'] = data.get('primary_dx') or p.diagnosis
        if not data.get('camper_name'):
            self.add_error('camper_name', 'Enter the camper name or choose a camper.')
        if not data.get('no_treatment_ordered') and not data.get('treatment_ordered'):
            self.add_error('treatment_ordered', 'Describe the treatment ordered, or tick "No treatment ordered".')
        return data


class CrewCheckInForm(RecordForm):
    medical_person_signature = SignatureField(label='Medical person signature')
    crew_signature = SignatureField(label='Camp crew signature')
    sections = [
        ('Crew member', ['name', 'date_of_birth', 'date']),
        ('Medical', ['has_allergies', 'allergies', 'medication', 'broviac_portacath', 'blood_count', 'comments']),
        ('Signatures', ['medical_person_name', 'medical_person_signature', 'crew_signature']),
    ]

    class Meta:
        model = CrewCheckIn
        exclude = ['created_at', 'created_by']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                   'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}


class CrewIndemnityForm(RecordForm):
    signature = SignatureField(label='Crew member signature')
    witness_signature = SignatureField(label='Witness signature')
    sections = [
        ('Crew member', ['full_name', 'id_number', 'camp_dates', 'camp_venue']),
        ('Signing', ['signed_at_place', 'date', 'signature', 'witness_name', 'witness_signature']),
    ]

    class Meta:
        model = CrewIndemnity
        exclude = ['created_at', 'created_by']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}
