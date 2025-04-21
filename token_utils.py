import gspread
import json
from kiteconnect import KiteConnect
from oauth2client.service_account import ServiceAccountCredentials


def load_credentials_from_gsheet(secrets, worksheet_name="ZerodhaTokenStore"):
    """
    Load API credentials from a Google Sheet.
    Returns api_key, api_secret, access_token, valid_token
    """
    try:
        credentials = json.loads(secrets["gcp_service_account"])
        spreadsheet_url = secrets["spreadsheet_url"]

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(spreadsheet_url).worksheet(worksheet_name)

        records = sheet.get_all_records()
        creds_map = {row['Key']: row['Value'] for row in records if 'Key' in row and 'Value' in row}

        api_key = creds_map.get("api_key")
        api_secret = creds_map.get("api_secret")
        access_token = creds_map.get("access_token")

        valid_token = False
        if api_key and api_secret and access_token:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            try:
                kite.profile()  # validate token
                valid_token = True
            except Exception:
                valid_token = False

        return api_key, api_secret, access_token, valid_token

    except Exception as e:
        raise RuntimeError(f"Failed to load credentials: {e}")
