from django import forms
from patients.forms import INPUT
from .models import CampNote


class CampNoteForm(forms.ModelForm):
    class Meta:
        model = CampNote
        fields = ['observation', 'incident_report', 'adherence_barrier_noted']
        widgets = {'observation': forms.Textarea(attrs={'rows': 4}),
                   'incident_report': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, can_file_incident=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not can_file_incident:
            del self.fields['incident_report']
        for name, f in self.fields.items():
            if name != 'adherence_barrier_noted':
                f.widget.attrs['class'] = INPUT
