# JFF Cloud Oncology Records (CHRS look and role model)

Django + PostgreSQL on Google Cloud Run. The interface and role matrix follow the offline Camp Health
Records System (CHRS): warm paper background, teal clinical actions, red allergy banner, Camp Footprints
lime/brown accents, Admin / Physician / Nurse / Counselor roles, idle-lock screen and an append-only audit log.

## The seven JFF forms (all digitised, drawn signatures)
1. Camper Registration and Indemnity (register page, signed indemnity + witness)
2. Camper Medication Check-In and Assessment (/forms/checkin/)
3. Medications and Treatments weekly record (patient page > Weekly medication record)
4. Medication / Treatment Event / Near Miss (/forms/nearmiss/, locked once filed)
5. Visit to MedShack (/forms/medshack/)
6. Medical Centre Check-In: Staff / Crew (/forms/crew-checkin/, Physician/Nurse only)
7. Camp Crew Indemnity and Media Release (/forms/crew-indemnity/, Physician/Nurse only)

## Features
- Dashboard: search, missed-dose alert, counts, patients with allergies, latest notes
- Patients: list/search, record with red clinical-alert banner, register, edit, CSV import
- Camp notes: daily observations, incident reports (Physician/Nurse only), adherence-barrier flag
- Medication log: schedule doses, "Mark given", automatic missed-dose flag (60 min grace for late doses)
- Role-based access via Django Groups; permissions in `accounts/rbac.py` mirror CHRS `rbac.ts`
- Audit log (Physician): logins, failed logins, views, edits, denied access, unlock attempts
- Idle lock after `INACTIVITY_LOCK_SECONDS` (default 600 s); sessions expire after 30 min

## Role matrix
| Permission | Admin | Physician | Nurse | Counselor |
|---|---|---|---|---|
| View clinical records | yes | yes | yes | yes |
| Edit records / mark doses / add notes | no | yes | yes | no |
| File incident reports | no | yes | yes | no |
| Import CSV | yes | yes | no | no |
| View audit log | no | yes | no | no |
| Manage users (/admin/) | yes | no | no | no |

## Run locally
    pip install -r requirements.txt
    USE_SQLITE=1 python manage.py migrate
    USE_SQLITE=1 python manage.py seed_demo --password 'choose-a-password'
    USE_SQLITE=1 python manage.py runserver
Demo users: admin, physician, nurse, counselor.

## Deploy (existing Cloud Run + Cloud SQL setup)
1. Run `python manage.py migrate` against Cloud SQL (adds allergies, medical notes, audit table, role groups).
2. Create real staff in `/admin/` (a superuser counts as Admin) and put each in one role group.
   Do not use `seed_demo` passwords in production.
3. Rebuild and deploy the container. Set `SECRET_KEY` and `DEBUG=False` as Cloud Run variables.

## Rebuild the stylesheet (only if you add new CSS classes to templates)
    npx tailwindcss@3 -c assets/tailwind.config.js -i assets/input.css -o static/css/chrs.css --minify
