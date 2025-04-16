import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import datetime as dt

st.set_page_config(layout="wide")
st.title("📊 BANKNIFTY Token Manager + Index Fetcher")

# --- Step 1: Authenticate with Google Sheets ---
st.subheader("🔐 Zerodha API Token Setup")

# Load Google credentials from Streamlit Secrets
try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    sheet_ok = True
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")
    sheet_ok = False

# --- Step 2: Accept API Key and Secret ---
api_key = st.text_input("🔑 API Key")
api_secret = st.text_input("🔒 API Secret", type="password")

# --- Step 3: Generate login URL ---
if api_key and api_secret:
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()
    st.markdown(f"🔗 [Login to Zerodha and get `request_token`]({login_url})")

    request_token = st.text_input("📥 Paste request_token from URL")

    if request_token:
        try:
            session = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session["access_token"]
            st.success("✅ Access token generated successfully!")
            st.code(access_token)

            # Save to Google Sheet
            if st.button("💾 Save token to Google Sheet"):
                if sheet_ok:
                    sheet.update("A1", api_key)
                    sheet.update("B1", api_secret)
                    sheet.update("C1", access_token)
                    st.success("✅ Token saved to Google Sheet.")
                else:
                    st.error("❌ Google Sheet connection not established.")

        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")

# --- Step 4: Fetch BANKNIFTY Index using saved token ---
st.markdown("---")
st.subheader("📈 BANKNIFTY Price Fetch (using saved token)")

if sheet_ok:
    try:
        tokens = sheet.row_values(1)
        saved_api_key = tokens[0]
        saved_api_secret = tokens[1]
        saved_access_token = tokens[2]

        kite = KiteConnect(api_key=saved_api_key)
        kite.set_access_token(saved_access_token)

        if st.button("📊 Get Current BANKNIFTY Price"):
            quote = kite.quote(["NSE:NIFTY BANK"])
            last_price = quote["NSE:NIFTY BANK"]["last_price"]
            st.success(f"✅ BANKNIFTY Spot Index: {last_price}")

    except Exception as e:
        st.error(f"❌ Failed to fetch BANKNIFTY price: {e}")
else:
    st.info("ℹ️ Token cannot be used until Google Sheet is accessible.")
