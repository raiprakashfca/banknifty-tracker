import streamlit as st
from kiteconnect import KiteConnect
import datetime as dt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from tracker import get_all_returns, analyze_contribution

st.set_page_config(page_title="BANKNIFTY Tracker", layout="wide")
st.title("📊 BANKNIFTY Component Impact Tracker")

# Section 1: Load credentials from Google Sheets (ZerodhaTokenStore)
st.header("🔐 Loading Zerodha credentials from Google Sheets")

try:
    credentials = json.loads(st.secrets["gcp_service_account"])
    spreadsheet_url = st.secrets["spreadsheet_url"]

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).worksheet("ZerodhaTokenStore")

    # Read values
    records = sheet.get_all_records()
    creds_map = {row['Key']: row['Value'] for row in records if 'Key' in row and 'Value' in row}

    api_key = creds_map.get("api_key")
    api_secret = creds_map.get("api_secret")
    access_token = creds_map.get("access_token")

    if not api_key or not api_secret or not access_token:
        st.error("❌ Missing credentials in the sheet. Please make sure api_key, api_secret, and access_token are present.")
    else:
        st.success("✅ Zerodha credentials loaded successfully from Google Sheet")

        # Run analysis section
        st.header("📈 BANKNIFTY Contribution Analysis")

        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
        with col2:
            to_date = st.date_input("To Date", dt.date.today())

        if st.button("Run Analysis"):
            st.info("🔄 Fetching data and analyzing...")
            try:
                df = get_all_returns(api_key, access_token, from_date, to_date)
                summary = analyze_contribution(df, as_text=True)
                st.success("✅ Analysis complete.")
                st.text_area("Regression Output", summary, height=400)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

except Exception as e:
    st.error(f"🚨 Failed to load credentials from Google Sheets: {e}")

# Rename canvas to match file
# canvas rename: app.py
