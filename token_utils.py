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

        data = sheet.get_all_records()
        if not data:
            raise ValueError("Sheet is empty")

        row = data[0]  # Use the first row
        api_key = row.get("api_key")
        api_secret = row.get("api_secret")
        access_token = row.get("access_token")
        last_updated = row.get("last_updated")

        # Optional validation logic
        valid_token = bool(access_token and len(access_token) > 20)

        return api_key, api_secret, access_token, valid_token

    except Exception as e:
        raise RuntimeError(f"Failed to load credentials: {e}")
