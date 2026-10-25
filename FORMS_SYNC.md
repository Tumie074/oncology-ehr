# Microsoft Forms sync

Set these Cloud Run variables, then redeploy (`gcloud run deploy oncology-ehr --source . --region africa-south1`)
or update them without rebuilding:

    gcloud run services update oncology-ehr --region africa-south1 --update-env-vars FORMS_EXPORT_URL="https://..."

| Variable | Meaning |
|---|---|
| FORMS_EXPORT_URL | https link that downloads the Forms response workbook (.xlsx) or a .csv |
| FORMS_AUTO_SYNC_MINUTES | how often the dashboard pulls (default 5, 0 = off) |
| FORMS_SYNC_TOKEN | secret for the optional Power Automate webhook /patients/forms-webhook/ |

Test the link: open it in a private browser window. It must start downloading the .xlsx. If it shows a web page, the
link will not work. Then open /patients/sync/ as Admin and press "Sync now".
