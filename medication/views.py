from datetime import timedelta
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.rbac import permission_required
from audit.models import log
from patients.models import Patient
from .forms import MedicationForm
from .models import MedicationRecord


@permission_required('VIEW_CLINICAL_RECORDS')
def schedule(request):
    MedicationRecord.refresh_missed()
    qs = MedicationRecord.objects.select_related('patient')
    now = timezone.now()
    return render(request, 'medication/schedule.html', {
        'missed': qs.filter(administered_time__isnull=True, missed=True).order_by('scheduled_time'),
        'upcoming': qs.filter(administered_time__isnull=True, missed=False).order_by('scheduled_time')[:50],
        'given': qs.filter(administered_time__isnull=False).order_by('-administered_time')[:25],
        'now': now,
    })


@permission_required('EDIT_CLINICAL_RECORDS')
def add_medication(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = MedicationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        n = form.cleaned_data['repeat_days']
        first = form.cleaned_data['scheduled_time']
        for i in range(n):
            MedicationRecord.objects.create(patient=patient, medication_name=form.cleaned_data['medication_name'], dosage=form.cleaned_data['dosage'],
                                            scheduled_time=first + timedelta(days=i), notes=form.cleaned_data['notes'])
        log(request, 'MED_SCHEDULE', f'{patient.case_number} {form.cleaned_data["medication_name"]} x{n}')
        messages.success(request, f'{n} dose{"s" if n > 1 else ""} scheduled.')
        return redirect('patient_medlog', pk=pk)
    return render(request, 'medication/form.html', {'form': form, 'patient': patient})


@require_POST
@permission_required('EDIT_CLINICAL_RECORDS')
def administer(request, pk):
    rec = get_object_or_404(MedicationRecord, pk=pk)
    if not rec.administered_time:
        rec.administer(request.user.get_full_name() or request.user.get_username())
        note = request.POST.get('note', '').strip()
        if note:
            rec.notes = (rec.notes + '\n' if rec.notes else '') + note
            rec.save()
        log(request, 'MED_ADMINISTER', f'{rec.patient.case_number} {rec.medication_name} ({rec.status})')
        messages.success(request, f'{rec.medication_name} recorded as given to {rec.patient.full_name}.')
    return redirect(request.POST.get('next') or 'medication_schedule')


@permission_required('VIEW_CLINICAL_RECORDS')
def weekly(request, pk):
    """Medications and Treatments: the weekly dose record for one patient."""
    patient = get_object_or_404(Patient, pk=pk)
    MedicationRecord.refresh_missed()
    try:
        offset = int(request.GET.get('w', 0))
    except ValueError:
        offset = 0
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    days = [monday + timedelta(days=i) for i in range(7)]
    start = timezone.make_aware(timezone.datetime.combine(monday, timezone.datetime.min.time()))
    recs = patient.medication_records.filter(scheduled_time__gte=start, scheduled_time__lt=start + timedelta(days=7)).order_by('scheduled_time')
    rows = {}
    for r in recs:
        local = timezone.localtime(r.scheduled_time)
        key = (r.medication_name, r.dosage, local.strftime('%H:%M'))
        rows.setdefault(key, {d: [] for d in days})[local.date()].append(r)
    grid = [dict(name=k[0], dose=k[1], time=k[2], cells=[v[d] for d in days]) for k, v in sorted(rows.items(), key=lambda kv: (kv[0][2], kv[0][0]))]
    log(request, 'MEDLOG_VIEW', patient.case_number)
    return render(request, 'medication/weekly.html', {'patient': patient, 'days': days, 'grid': grid, 'offset': offset, 'today': today})
