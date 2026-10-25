# Cloud-Based Oncology Records System

A cloud-based electronic health record (EHR) system for a non-profit organisation (NPO) that runs camps for
children with cancer and other serious illness. It replaces paper forms and spreadsheets with one role-controlled,
auditable record.

Built for **ITRI671 (Honours IT, North-West University)** by Itumeleng Ntela (43528309) as the artefact of a
Design Science Research study. Supervisor: Prof. Janet Liebenberg.

> **Demo data only.** This repository and the live demo contain invented patients. Do not enter real personal information.

## What it does
- **Patient records** with a red clinical-alert banner for allergies and medical precautions; search, edit, CSV import
- **Medication log** with scheduled doses, "Mark given" and an automatic **missed-dose flag** (60-minute grace period).
  The flag is updated when a page is opened; there are no push alerts yet
- **Camp notes** and incident notes
- **Seven digital forms** replacing the NPO's paper forms, with drawn signatures: registration and indemnity,
  medication check-in, weekly medication record, near-miss event, medical-centre visit, crew check-in, crew indemnity
- **Four roles** (Admin, Physician, Nurse, Counselor) with their own permissions
- **Audit log** of logins, views, edits and refused actions (POPIA accountability)
- **Microsoft Forms sync**: families register on an online Microsoft Form; an Admin or Physician uploads the exported
  responses and the system creates new patients (see below)
- Idle-lock screen after 10 minutes; sessions expire after 30 minutes

## Role matrix
| Permission | Admin | Physician | Nurse | Counselor |
|---|---|---|---|---|
| View clinical records | yes | yes | yes | yes |
| Edit records, mark doses, add notes | no | yes | yes | no |
| File incident / near-miss reports | no | yes | yes | no |
| Import CSV, sync from Microsoft Forms | yes | yes | no | no |
| View audit log | no | yes | no | no |
| Manage users (`/admin/`) | yes | no | no | no |

## Microsoft Forms sync (automatic)
Registration happens outside the system on a Microsoft Form; the system pulls the responses in by itself.
1. Build a Form with these questions: child's first name, last name, date of birth, diagnosis, allergies (optional),
   medical notes (optional), guardian's name, guardian's contact number.
2. In Forms: Responses > Open in Excel. Share that workbook ("Anyone with the link can view") and copy a direct download
   link (it must download the `.xlsx` when opened in a private browser window).
3. Set the Cloud Run variable `FORMS_EXPORT_URL` to that link (optionally `FORMS_AUTO_SYNC_MINUTES`, default 5).

The dashboard then pulls new registrations at most every 5 minutes, and **Sync now** (`/patients/sync/`, Admin or
Physician) does it on demand. A file upload remains as a fallback, with a *Preview only* option.
Optional push: a Power Automate flow ("When a new response is submitted" then HTTP POST) can call
`/patients/forms-webhook/` with header `X-Sync-Token` (set `FORMS_SYNC_TOKEN`) and the answers as JSON keyed by question.

New children get case numbers `MF-001`, `MF-002`, ...; a child with the same name and date of birth is skipped, so repeated
syncs are safe; every row passes the normal patient validation; all syncs are audit-logged.
Use dummy data only: a shared link lets anyone holding it read the workbook, which is not acceptable for real health data.
For production use a Microsoft Graph connection or the token-protected webhook instead.

## Technology
Django 6 and PostgreSQL, hosted on Google Cloud Run with Cloud SQL in the Johannesburg region (`africa-south1`) so that
personal information stays in South Africa (POPIA). Static files are served with WhiteNoise; styling is Tailwind CSS.

## Run locally
    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    export USE_SQLITE=1                                      # Windows: set USE_SQLITE=1
    python manage.py migrate
    python manage.py seed_demo --password 'choose-a-password'
    python manage.py runserver
Demo users created by `seed_demo`: `admin`, `physician`, `nurse`, `counselor`.

## Deploy (Google Cloud Run)
    gcloud run deploy oncology-ehr --source . --region africa-south1
Database settings are kept as Cloud Run environment variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SOCKET_HOST`,
`DB_PORT`), together with `SECRET_KEY` and `DEBUG=False`. Never commit them. The container runs `migrate` on start.
Create real staff in `/admin/` and put each in one role group; do not use `seed_demo` passwords in production.

## Limitations
One organisation, one main informant and one acceptance reviewer; evaluated with dummy data; efficiency was not
measured; missed-dose flags appear on page load, not as alerts; no incident summary report and no offline mode.
Planned: medication prescription record, offline mode, audit reporting for POPIA, a camp trial.

## Project structure
`accounts` (roles, login, dashboard) · `patients` (records, registration, CSV and Forms sync) · `medication` ·
`campnotes` · `records` (the seven forms) · `audit` · `core` (settings) · `templates` · `static`
