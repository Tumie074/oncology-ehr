import csv
import io
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.rbac import permission_required
from audit.models import log
from campnotes.models import CampNote
from medication.models import MedicationRecord
from . import forms_sync
from .forms import CSVImportForm, FormsSyncForm, PatientForm, PatientRegistrationForm
from .models import Patient

VIEW = 'VIEW_CLINICAL_RECORDS'
EDIT = 'EDIT_CLINICAL_RECORDS'


@permission_required(VIEW)
def patient_list(request):
    q = request.GET.get('q', '').strip()
    patients = Patient.objects.all()
    if q:
        patients = patients.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                                   Q(case_number__icontains=q) | Q(diagnosis__icontains=q))
    log(request, 'PATIENT_SEARCH' if q else 'PATIENT_LIST', q)
    return render(request, 'patients/list.html', {'patients': patients, 'q': q})


@permission_required(VIEW)
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    MedicationRecord.refresh_missed()
    log(request, 'PATIENT_VIEW', patient.case_number)
    return render(request, 'patients/detail.html', {
        'patient': patient,
        'notes': patient.camp_notes.order_by('-date_recorded', '-id')[:10],
        'meds': patient.medication_records.order_by('-scheduled_time')[:15],
        'checkins': patient.checkins.all()[:5],
        'visits': patient.medshack_visits.all()[:5],
        'nearmisses': patient.near_misses.all()[:5],
        'now': timezone.now(),
    })


@permission_required(EDIT)
def register_patient(request):
    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient = form.save()
        log(request, 'PATIENT_REGISTER', patient.case_number)
        return redirect('register_success', pk=patient.pk)
    return render(request, 'patients/register.html', {'form': form, 'title': 'Register patient'})


@permission_required(VIEW)
def register_success(request, pk):
    return render(request, 'patients/success.html', {'patient': get_object_or_404(Patient, pk=pk)})


@permission_required(EDIT)
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log(request, 'PATIENT_EDIT', patient.case_number)
        messages.success(request, 'Patient record updated.')
        return redirect('patient_detail', pk=pk)
    return render(request, 'patients/register.html', {'form': form, 'title': f'Edit {patient.full_name}', 'editing': True})


@permission_required('IMPORT_CSV')
def import_csv(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == 'POST' and form.is_valid():
        text = io.TextIOWrapper(form.cleaned_data['file'].file, encoding='utf-8-sig')
        created = skipped = 0
        errors = []
        for n, row in enumerate(csv.DictReader(text), start=2):
            f = PatientForm({k.strip(): (v or '').strip() for k, v in row.items() if k})
            if f.is_valid():
                f.save()
                created += 1
            else:
                skipped += 1
                errors.append(f'Row {n}: ' + '; '.join(f'{k} {", ".join(v)}' for k, v in f.errors.items()))
        log(request, 'CSV_IMPORT', f'{created} created, {skipped} skipped')
        result = {'created': created, 'skipped': skipped, 'errors': errors[:15]}
    return render(request, 'patients/import.html', {'form': form, 'result': result})


@permission_required('IMPORT_CSV')
def forms_sync_view(request):
    form = FormsSyncForm(request.POST or None, request.FILES or None)
    result = error = None
    if request.method == 'POST' and form.is_valid():
        preview = form.cleaned_data['preview']
        try:
            result = forms_sync.sync(form.cleaned_data['file'], save=not preview)
        except ValueError as e:
            error = str(e)
        else:
            if preview:
                log(request, 'FORMS_SYNC_PREVIEW', f"{result['created']} would be created")
            else:
                log(request, 'FORMS_SYNC', f"{result['created']} created, {result['present']} already present, {result['skipped']} skipped")
    return render(request, 'patients/forms_sync.html', {'form': form, 'result': result, 'error': error})
