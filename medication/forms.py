from django import forms
from patients.forms import INPUT
from .models import MedicationRecord


class MedicationForm(forms.ModelForm):
    repeat_days = forms.IntegerField(min_value=1, max_value=28, initial=1, label='Repeat daily for (days)', help_text='1 = a single dose. Use 7 to fill the weekly record.')

    class Meta:
        model = MedicationRecord
        fields = ['medication_name', 'dosage', 'scheduled_time', 'notes']
        widgets = {'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
                   'notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = INPUT
