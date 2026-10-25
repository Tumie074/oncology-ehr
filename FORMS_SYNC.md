# Microsoft Forms sync

Families register on a Microsoft Form. An Admin or Physician then syncs the responses into the system.

1. Forms > your form > Responses > Open in Excel (download the .xlsx).
2. System dashboard > "Sync from Microsoft Forms" (/patients/sync/) > choose the file.
3. Tick "Preview only" first to see how the questions were matched, then untick and sync.

Rules: new children get case numbers MF-001, MF-002 ...; a child with the same first name, last name and date of birth
is skipped (safe to upload the same export again); every row goes through the normal patient validation;
required columns are first name, last name, date of birth, diagnosis, guardian name, guardian contact.
Questions are matched by their wording (e.g. "Child's first name", "Date of birth", "Guardian's contact number"); the
page shows the matching after each upload. Only Admin and Physician can sync. Each sync is written to the audit log.

Deploy: the new dependency openpyxl is in requirements.txt, so rebuild/redeploy as usual (no database migration).
