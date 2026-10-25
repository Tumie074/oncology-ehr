import json
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.rbac import has_permission, permission_required
from audit.models import log
from patients.models import Patient
from . import forms as F
from .models import CamperCheckIn, CrewCheckIn, CrewIndemnity, MedShackVisit, NearMissReport

VIEW, EDIT, INCIDENT = 'VIEW_CLINICAL_RECORDS', 'EDIT_CLINICAL_RECORDS', 'FILE_INCIDENT_REPORT'

KINDS = {
    'checkin': dict(model=CamperCheckIn, form=F.CamperCheckInForm, title='Camper Medication Check-In and Assessment',
                    blurb='Physical condition, medication, accessibility, TB screening and medical sign-off.',
                    new=EDIT, view=VIEW, patient=True, cols=['patient', 'assessed_at', 'medical_person_name']),
    'medshack': dict(model=MedShackVisit, form=F.MedShackVisitForm, title='Visit to MedShack',
                     blurb='Vital signs, symptoms, findings, treatments and nurse / doctor signatures.',
                     new=EDIT, view=VIEW, patient=True, cols=['patient', 'visit_at', 'reason']),
    'nearmiss': dict(model=NearMissReport, form=F.NearMissForm, title='Medication / Treatment Event / Near Miss',
                     blurb='Locked once filed. Event, response, reporter signature and investigation.',
                     new=INCIDENT, view=VIEW, patient=True, cols=['camper_name', 'event_at', 'reporter_name']),
    'crew-checkin': dict(model=CrewCheckIn, form=F.CrewCheckInForm, title='Medical Centre Check-In: Staff / Crew',
                         blurb='Stored separately from camper records.',
                         new=EDIT, view=EDIT, patient=False, cols=['name', 'date', 'medical_person_name']),
    'crew-indemnity': dict(model=CrewIndemnity, form=F.CrewIndemnityForm, title='Camp Crew Indemnity and Media Release',
                           blurb='Signed by each crew member and a witness. Stored with staff records.',
                           new=EDIT, view=EDIT, patient=False, cols=['full_name', 'camp_dates', 'date']),
}


def _kind(kind):
    cfg = KINDS.get(kind)
    if not cfg:
        raise Http404
    return cfg


def _require(request, perm):
    from django.core.exceptions import PermissionDenied
    if not has_permission(request.user, perm):
        log(request, 'ACCESS_DENIED', f'{perm} on {request.path}')
        raise PermissionDenied


def _label(model, name):
    return str(model._meta.get_field(name).verbose_name).replace('_', ' ').capitalize()


def _row(obj, cfg, name):
    v = getattr(obj, name)
    if name == 'patient' and v:
        return str(v)
    return v


@permission_required(VIEW)
def hub(request):
    cards = [dict(kind=k, **{x: c[x] for x in ('title', 'blurb')}, can_new=has_permission(request.user, c['new']),
                  can_view=has_permission(request.user, c['view']), count=c['model'].objects.count() if has_permission(request.user, c['view']) else None)
             for k, c in KINDS.items()]
    return render(request, 'records/hub.html', {'cards': cards})


def form_list(request, kind):
    cfg = _kind(kind)
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    _require(request, cfg['view'])
    objs = cfg['model'].objects.all()[:200]
    rows = [(o, [_row(o, cfg, c) for c in cfg['cols']]) for o in objs]
    log(request, 'FORM_LIST', kind)
    return render(request, 'records/list.html', {'kind': kind, 'cfg': cfg, 'headers': [_label(cfg['model'], c) for c in cfg['cols']], 'rows': rows,
                                                  'can_new': has_permission(request.user, cfg['new'])})


def _treatments_from_post(post):
    t, tr, o = post.getlist('treat_time'), post.getlist('treat_treatment'), post.getlist('treat_outcome')
    return [{'time': a.strip(), 'treatment': b.strip(), 'outcome': c.strip()} for a, b, c in zip(t, tr, o) if a.strip() or b.strip() or c.strip()]


def form_new(request, kind):
    cfg = _kind(kind)
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    _require(request, cfg['new'])
    initial = {}
    pid = request.GET.get('patient')
    if pid and cfg['patient']:
        p = Patient.objects.filter(pk=pid).first()
        if p:
            initial['patient'] = p
            if kind == 'nearmiss':
                initial.update(camper_name=p.full_name, date_of_birth=p.date_of_birth, primary_dx=p.diagnosis)
            if kind == 'medshack':
                initial.update(sex=p.get_sex_display() if p.sex else '')
            if kind == 'checkin':
                initial.update(eyesight=p.eyesight, hearing=p.hearing, mobility_aids=p.mobility_aids, prosthesis=p.prosthesis, dietary_requirements=p.dietary_requirements,
                               assist_bathing=p.assist_bathing, assist_dressing=p.assist_dressing, assist_toileting=p.assist_toileting, assist_eating=p.assist_eating)
    if kind == 'nearmiss':
        initial.setdefault('reporter_name', request.user.get_full_name() or request.user.get_username())
    form = cfg['form'](request.POST or None, initial=initial)
    if kind in ('checkin', 'crew-checkin') and 'medical_person_name' in form.fields:
        form.fields['medical_person_name'].initial = request.user.get_full_name() or request.user.get_username()
    treat_rows = _treatments_from_post(request.POST) if request.method == 'POST' else [{}]
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        if kind == 'medshack':
            obj.treatments = treat_rows
        if kind == 'nearmiss':
            obj.event_types = form.cleaned_data['event_types']
            obj.contributing_factors = form.cleaned_data['contributing_factors']
            obj.camper_name = form.cleaned_data['camper_name']
            obj.date_of_birth = form.cleaned_data['date_of_birth']
            obj.primary_dx = form.cleaned_data['primary_dx']
        obj.save()
        form.save_m2m()
        log(request, 'FORM_FILED', f'{kind} #{obj.pk}')
        messages.success(request, f'{cfg["title"]} saved.')
        return redirect('form_detail', kind=kind, pk=obj.pk)
    return render(request, 'records/form.html', {'kind': kind, 'cfg': cfg, 'form': form, 'treat_rows': treat_rows or [{}]})


def form_detail(request, kind, pk):
    cfg = _kind(kind)
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    _require(request, cfg['view'])
    obj = get_object_or_404(cfg['model'], pk=pk)
    fields = []
    for f in cfg['model']._meta.fields:
        if f.name in ('id', 'created_at', 'created_by', 'treatments'):
            continue
        v = getattr(obj, f.name)
        label = _label(cfg['model'], f.name)
        if 'signature' in f.name:
            if v:
                fields.append(dict(label=label, sig=v))
            continue
        if f.name == 'patient':
            v = obj.patient
        if isinstance(v, bool):
            v = 'Yes' if v else 'No'
        if v in (None, '', []):
            continue
        fields.append(dict(label=label, value=v))
    extra = []
    for f in cfg['model']._meta.get_fields():
        if f.name in ('event_types', 'contributing_factors') and getattr(obj, f.name):
            extra.append(dict(label=_label(cfg['model'], f.name), value=', '.join(getattr(obj, f.name))))
    fields = [x for x in fields if x.get('label') not in [e['label'] for e in extra]]
    fields += extra
    log(request, 'FORM_VIEW', f'{kind} #{pk}')
    return render(request, 'records/detail.html', {'kind': kind, 'cfg': cfg, 'obj': obj, 'fields': fields,
                                                    'treatments': obj.treatments if kind == 'medshack' else None})
