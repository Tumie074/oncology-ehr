import json
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from audit.models import AuditEvent, log
from campnotes.models import CampNote
from medication.models import MedicationRecord
from patients.models import Patient
from .rbac import permission_required


class CHRSLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    MedicationRecord.refresh_missed()
    today = timezone.localdate()
    missed = MedicationRecord.objects.select_related('patient').filter(
        administered_time__isnull=True, missed=True).order_by('scheduled_time')
    return render(request, 'accounts/dashboard.html', {
        'n_patients': Patient.objects.count(),
        'n_missed': missed.count(),
        'n_notes_today': CampNote.objects.filter(date_recorded=today).count(),
        'n_incidents': CampNote.objects.exclude(incident_report='').count(),
        'missed': missed[:8],
        'alert_patients': [p for p in Patient.objects.all() if p.has_alerts][:6],
        'recent_notes': CampNote.objects.select_related('patient').order_by('-date_recorded', '-id')[:5],
    })


@require_POST
@login_required
def unlock(request):
    """Re-authenticate after the inactivity lock (CHRS LockScreenModal)."""
    pw = request.POST.get('password', '')
    ok = request.user.check_password(pw)
    log(request, 'SESSION_UNLOCK' if ok else 'SESSION_UNLOCK_FAILED')
    return JsonResponse({'ok': ok})


@permission_required('VIEW_AUDIT_LOGS')
def audit_log(request):
    q = request.GET.get('q', '').strip()
    events = AuditEvent.objects.all()
    if q:
        events = events.filter(username__icontains=q) | events.filter(action__icontains=q) | events.filter(detail__icontains=q)
    return render(request, 'audit/list.html', {'events': events.order_by('-timestamp')[:300], 'q': q})
