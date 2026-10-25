"""Sync of child registrations collected on Microsoft Forms.

A Microsoft Forms response export (Excel .xlsx or .csv) is read, its question titles are matched to
patient fields, new children get a case number, children already in the system are skipped, and the
rest are saved through the normal PatientForm so every validation rule still applies.
"""
import csv
import datetime as dt
import io
import re

from .forms import PatientForm
from .models import Patient

# Ordered rules: most specific first. A column is given to the first field whose rule matches it.
RULES = [
    ('case_number', [['case number'], ['case no'], ['case id']]),
    ('emergency_contact_cell', [['emergency', 'cell'], ['emergency', 'number'], ['emergency', 'phone'], ['emergency', 'contact no']]),
    ('emergency_contact_name', [['emergency']]),
    ('relationship_to_child', [['relationship']]),
    ('guardian_contact', [['guardian', 'cell'], ['guardian', 'contact'], ['guardian', 'phone'], ['guardian', 'number'],
                          ['parent', 'cell'], ['parent', 'contact'], ['parent', 'phone'], ['parent', 'number'],
                          ['caregiver', 'cell'], ['caregiver', 'contact'], ['caregiver', 'phone'], ['caregiver', 'number']]),
    ('guardian_name', [['guardian'], ['parent'], ['caregiver']]),
    ('first_name', [['first name'], ['firstname'], ['given name'], ['child name'], ['name of child']]),
    ('last_name', [['last name'], ['lastname'], ['surname'], ['family name']]),
    ('date_of_birth', [['date of birth'], ['birth date'], ['birthday'], ['dob']]),
    ('diagnosis', [['diagnosis']]),
    ('allergies', [['allerg']]),
    ('medical_notes', [['medical notes'], ['medical note'], ['precaution'], ['medical condition']]),
    ('sex', [['sex'], ['gender']]),
    ('language', [['language']]),
    ('religion', [['religion']]),
    ('tshirt_size', [['shirt']]),
    ('camp_session_date', [['camp session'], ['camp date']]),
    ('address', [['address']]),
    ('clinic_file_number', [['clinic file']]),
    ('current_medication', [['current medication']]),
    ('dietary_requirements', [['dietary'], ['diet']]),
]
LABELS = {f: f.replace('_', ' ') for f, _ in RULES}
REQUIRED = ['first_name', 'last_name', 'date_of_birth', 'diagnosis', 'guardian_name', 'guardian_contact']
PREFIX = 'MF-'


def norm(h):
    return re.sub(r'[^a-z0-9]+', ' ', str(h or '').lower()).strip()


def map_columns(headers):
    """Return ({column index: field}, [unmatched header texts])."""
    mapping, used = {}, set()
    normed = [norm(h) for h in headers]
    for i, h in enumerate(normed):                       # exact field names win (CSV written for the system)
        for field, _ in RULES:
            if h == field.replace('_', ' ') and field not in used and i not in mapping:
                mapping[i] = field; used.add(field)
    for field, alts in RULES:
        if field in used:
            continue
        for i, h in enumerate(normed):
            if i in mapping or not h:
                continue
            if any(all(k in h for k in alt) for alt in alts):
                mapping[i] = field; used.add(field); break
    skip = {'id', 'start time', 'completion time', 'email', 'name', 'last modified time'}
    unmatched = [str(headers[i]) for i in range(len(headers)) if i not in mapping and norm(headers[i]) not in skip and str(headers[i] or '').strip()]
    return mapping, unmatched


def read_rows(upload):
    """Return (headers, rows) from an .xlsx or .csv upload."""
    name = (upload.name or '').lower()
    if name.endswith('.xlsx'):
        try:
            from openpyxl import load_workbook
        except ImportError:  # pragma: no cover
            raise ValueError('Excel files need the openpyxl package. Save the sheet as CSV and upload that instead.')
        wb = load_workbook(upload, read_only=True, data_only=True)
        data = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    elif name.endswith('.csv'):
        data = list(csv.reader(io.TextIOWrapper(upload.file, encoding='utf-8-sig')))
    else:
        raise ValueError('Upload the Microsoft Forms export as .xlsx, or a .csv file.')
    data = [r for r in data if any(str(c).strip() for c in r if c is not None)]
    if not data:
        raise ValueError('The file has no rows.')
    return data[0], data[1:]


def parse_date(v):
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    s = str(v or '').strip()
    if not s:
        return ''
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %B %Y', '%d %b %Y', '%m/%d/%Y'):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s


def clean_value(field, v):
    if field in ('date_of_birth', 'camp_session_date'):
        return parse_date(v)
    s = '' if v is None else str(v).strip()
    if field == 'sex':
        s = {'female': 'F', 'f': 'F', 'girl': 'F', 'male': 'M', 'm': 'M', 'boy': 'M'}.get(s.lower(), 'O' if s else '')
    if field in ('guardian_contact', 'emergency_contact_cell') and re.fullmatch(r'\d{9}', s):
        s = '0' + s                                     # Excel drops a leading zero from numbers
    if re.fullmatch(r'\d+\.0', s):
        s = s[:-2]
    return s


def next_case_number():
    nums = [int(c[len(PREFIX):]) for c in Patient.objects.filter(case_number__startswith=PREFIX).values_list('case_number', flat=True)
            if c[len(PREFIX):].isdigit()]
    return max(nums, default=0) + 1


def sync(upload, save=True):
    headers, rows = read_rows(upload)
    mapping, unmatched = map_columns(headers)
    mapped = set(mapping.values())
    missing = [f for f in REQUIRED if f not in mapped]
    result = {'mapping': [(str(headers[i]), LABELS[f]) for i, f in mapping.items()], 'unmatched': unmatched,
              'missing': [LABELS[f] for f in missing], 'created': 0, 'present': 0, 'skipped': 0, 'errors': [], 'new': [], 'preview': not save}
    if missing:
        return result
    counter = next_case_number()
    for n, row in enumerate(rows, start=2):
        data = {f: clean_value(f, row[i] if i < len(row) else '') for i, f in mapping.items()}
        if Patient.objects.filter(first_name__iexact=data.get('first_name', ''), last_name__iexact=data.get('last_name', ''),
                                  date_of_birth=data.get('date_of_birth') or None).exists():
            result['present'] += 1
            continue
        if not data.get('case_number'):
            data['case_number'] = f'{PREFIX}{counter:03d}'
        form = PatientForm(data)
        if form.is_valid():
            if save:
                form.save()
            counter += 1
            result['created'] += 1
            result['new'].append(f"{data['case_number']}  {data['first_name']} {data['last_name']}")
        else:
            result['skipped'] += 1
            result['errors'].append(f'Row {n}: ' + '; '.join(f'{k} {", ".join(v)}' for k, v in form.errors.items()))
    result['errors'] = result['errors'][:15]
    return result
