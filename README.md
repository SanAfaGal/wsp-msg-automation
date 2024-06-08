
## <span style="color: #FFF;">Introduction</span>:
The project at hand is an application designed to manage and analyze customer and reseller data stored in Google Sheets spreadsheets. 

## Steps

1. Visit <a href="https://console.cloud.google.com/apis" style="color: #007bff;">Google Cloud Console</a>.
2. Create a new project (optional).
3. Click on the "Enable APIs & Services" button.
4. Enable the <span style="color: #28a745;">Google Drive API</span>.
5. Enable the <span style="color: #28a745;">Google Sheets API</span>.
6. Click on the "Create credentials" button.
7. Select "<span style="color: #6f42c1;">Service Account</span>".
8. Fill out the form.
9. Click on the newly created credential.
10. Copy the email.
11. Select the "<span style="color: #dc3545;">keys</span>" tab.
12. Add a new key.
13. Select the JSON type.
14. Open the Google Sheets file and share access with the <span style="color: #007bff;">client_email</span> of the service account

## Docs

- [Service Account Documentation](https://cloud.google.com/iam/docs/service-account-overview)
- [Best Practices for Managing Service Account Keys](https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)

## Advice

- Ensure that the name of the Google Sheet contains no spaces.
- Make sure that the sheet is not set to private access only.

## Run
Create a virtual environment and install packages:
```
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables:
Make sure you have the follow variables in your .env:
```
CHROME_PATH='.exe'
EDGE_PATH'.exe'
CREDS_PATH='.json'
SPREADSHEET_TITLE='SpreadSheet'
WORKSHEET_TITLE='WorkSheet'
ACCESS_SCOPES='scope_one,scope_two'
```
