import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


def load_credentials_from_gsheet(secrets, sheet_name="Sheet1"):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        google_creds = json.loads(secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
        client = gspread.authorize(creds)

        sheet_url = secrets["spreadsheet_url"]
        sheet = client.open_by_url(sheet_url).worksheet(sheet_name)

        values = sheet.get_all_values()
        if len(values) < 1:
            raise ValueError("Sheet is empty")

        row = values[0]
        if len(row) < 4:
            raise ValueError("Expected at least 4 columns in the first row")

        api_key = row[0].strip()
        api_secret = row[1].strip()
        access_token = row[2].strip()
        last_updated = row[3].strip()

        valid_token = bool(access_token and len(access_token) > 20)

        return api_key, api_secret, access_token, valid_token

    except Exception as e:
        raise RuntimeError(f"Failed to load credentials: {e}")
