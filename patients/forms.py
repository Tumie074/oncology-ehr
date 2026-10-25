from django import forms
from django.utils import timezone
from .models import Patient

INPUT = 'w-full border border-slate-300 rounded p-2 text-sm focus:outline-none focus:ring-2 focus:ring-clinical-500'


def style_fields(form):
    for name, f in form.fields.items():
        w = f.widget
        if isinstance(w, (forms.CheckboxInput, forms.HiddenInput)):
            continue
        w.attrs['class'] = INPUT


class SignatureField(forms.CharField):
    """A drawn signature, stored as a PNG data URL produced by the signature pad."""
    widget = forms.HiddenInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('error_messages', {'required': 'Please sign in the box.'})
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value and not value.startswith('data:image/png;base64,'):
            raise forms.ValidationError('Invalid signature.')
        if value and len(value) > 400_000:
            raise forms.ValidationError('Signature image is too large.')
        return value


class SectionedForm(forms.ModelForm):
    """ModelForm that can render itself in titled sections (see partials/fieldsets.html)."""
    sections = []

    def get_sections(self):
        for title, names in self.sections:
            yield title, [self[n] for n in names if n in self.fields]


class PatientForm(SectionedForm):
    sections = [
        ('Personal information', ['case_number', 'first_name', 'last_name', 'date_of_birth', 'sex', 'language', 'religion', 'tshirt_size', 'camp_session_date', 'address']),
        ('Parent / caregiver and emergency contact', ['guardian_name', 'guardian_contact', 'relationship_to_child', 'emergency_contact_name', 'emergency_contact_cell']),
        ('Medical information', ['diagnosis', 'allergies', 'medical_notes', 'clinic_file_number', 'clinic_contact_details', 'current_medication', 'medication_handed_in']),
        ('Clinical review', ['viral_load_over_1000', 'hepatitis_b', 'tb_history', 'adherence_barriers', 'tb_cough_2_weeks', 'tb_weight_loss', 'tb_night_sweats']),
        ('Accessibility and daily living', ['eyesight', 'hearing', 'mobility_aids', 'prosthesis', 'assist_bathing', 'assist_dressing', 'assist_toileting', 'assist_eating']),
        ('Additional information', ['dietary_requirements', 'behavioural_notes', 'additional_disclosures', 'linked_sibling']),
    ]

    class Meta:
        model = Patient
        fields = [n for _, names in [
            ('', ['case_number', 'first_name', 'last_name', 'date_of_birth', 'sex', 'language', 'religion', 'tshirt_size', 'camp_session_date', 'address',
                  'guardian_name', 'guardian_contact', 'relationship_to_child', 'emergency_contact_name', 'emergency_contact_cell',
                  'diagnosis', 'allergies', 'medical_notes', 'clinic_file_number', 'clinic_contact_details', 'current_medication', 'medication_handed_in',
                  'viral_load_over_1000', 'hepatitis_b', 'tb_history', 'adherence_barriers', 'tb_cough_2_weeks', 'tb_weight_loss', 'tb_night_sweats',
                  'eyesight', 'hearing', 'mobility_aids', 'prosthesis', 'assist_bathing', 'assist_dressing', 'assist_toileting', 'assist_eating',
                  'dietary_requirements', 'behavioural_notes', 'additional_disclosures', 'linked_sibling'])] for n in names]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'camp_session_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'medical_notes': forms.Textarea(attrs={'rows': 2}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'clinic_contact_details': forms.Textarea(attrs={'rows': 2}),
            'current_medication': forms.Textarea(attrs={'rows': 2}),
            'adherence_barriers': forms.Textarea(attrs={'rows': 2}),
            'behavioural_notes': forms.Textarea(attrs={'rows': 2}),
            'additional_disclosures': forms.Textarea(attrs={'rows': 2}),
            'allergies': forms.TextInput(attrs={'placeholder': 'Penicillin, Latex'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        if 'linked_sibling' in self.fields:
            qs = Patient.objects.all()
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields['linked_sibling'].queryset = qs
            self.fields['linked_sibling'].required = False


class PatientRegistrationForm(PatientForm):
    """Registration page: adds the signed indemnity and consent (required)."""
    indemnity_agree = forms.BooleanField(
        required=True, label='I have read and accept the indemnity and consent for Camp Footprints',
        error_messages={'required': 'The indemnity and consent must be accepted.'})
    indemnity_witness_name = forms.CharField(max_length=150, label='Witness name')
    indemnity_guardian_signature = SignatureField(label='Parent / guardian signature')
    indemnity_witness_signature = SignatureField(label='Witness signature')

    sections = PatientForm.sections + [
        ('Indemnity and consent (required)', ['indemnity_agree', 'indemnity_guardian_signature', 'indemnity_witness_name', 'indemnity_witness_signature']),
    ]

    class Meta(PatientForm.Meta):
        fields = PatientForm.Meta.fields + ['indemnity_witness_name', 'indemnity_guardian_signature', 'indemnity_witness_signature']

    def save(self, commit=True):
        p = super().save(commit=False)
        p.indemnity_signed = True
        p.indemnity_signed_at = timezone.now()
        if commit:
            p.save()
        return p


class CSVImportForm(forms.Form):
    file = forms.FileField(help_text='CSV with header: case_number, first_name, last_name, date_of_birth (YYYY-MM-DD), diagnosis, allergies, guardian_name, guardian_contact (other registration columns are optional)')


class FormsSyncForm(forms.Form):
    file = forms.FileField(label='Microsoft Forms export', help_text='In Microsoft Forms open Responses > Open in Excel, download the .xlsx and upload it here (a .csv also works).')
    preview = forms.BooleanField(required=False, label='Preview only (check the matching, do not save)')
