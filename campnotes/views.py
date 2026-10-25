from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.rbac import has_permission, permission_required
from audit.models import log
from patients.models import Patient
from .forms import CampNoteForm
from .models import CampNote


@permission_required('VIEW_CLINICAL_RECORDS')
def note_list(request):
    notes = CampNote.objects.select_related('patient').order_by('-date_recorded', '-id')
    if request.GET.get('incidents'):
        notes = notes.exclude(incident_report='')
    return render(request, 'campnotes/list.html', {'notes': notes[:100], 'incidents_only': bool(request.GET.get('incidents'))})


@permission_required('EDIT_CLINICAL_RECORDS')
def add_note(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = CampNoteForm(request.POST or None, can_file_incident=has_permission(request.user, 'FILE_INCIDENT_REPORT'))
    if request.method == 'POST' and form.is_valid():
        note = form.save(commit=False)
        note.patient = patient
        note.recorded_by = request.user.get_full_name() or request.user.get_username()
        note.save()
        log(request, 'NOTE_ADD', f'{patient.case_number}' + (' INCIDENT' if note.incident_report else ''))
        messages.success(request, 'Camp note saved.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'campnotes/form.html', {'form': form, 'patient': patient})
