import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Manager + BANKNIFTY Test")

# --- Step 1: Connect to Google Sheet ---
st.subheader("Step 1: Connect to Google Sheets")

sheet_ok = False
sheet = None

try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    sheet_ok = True
    st.success("✅ Connected to Google Sheet")
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheet: {e}")

# --- Step 2: Generate Zerodha Access Token ---
st.subheader("Step 2: Generate Zerodha Access Token")

api_key = st.text_input("🔑 API Key")
api_secret = st.text_input("🔒 API Secret", type="password")

if api_key and api_secret:
    try:
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        st.markdown(f"🔗 [Login to Zerodha and get `request_token`]({login_url})")
    except Exception as e:
        st.error(f"❌ Failed to generate login URL: {e}")

    request_token = st.text_input("📥 Paste request_token here")

    if request_token:
        try:
            session = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session["access_token"]
            st.success("✅ Access token generated!")
            st.code(access_token)

            # Save to sheet
            if st.button("💾 Save to Google Sheet"):
                try:
                    sheet.update("A1:C1", [[api_key, api_secret, access_token]])
                    st.success("✅ Token saved to Google Sheet")
                except Exception as e:
                    st.error(f"❌ Failed to save token: {e}")
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")
else:
    st.info("ℹ️ Enter your API Key and Secret to begin.")

# --- Step 3: Use Token to Get BANKNIFTY Price ---
st.markdown("---")
st.subheader("Step 3: Test Token - Get BANKNIFTY Index Price")

if sheet_ok:
    try:
        tokens = sheet.row_values(1)

        if len(tokens) < 3:
            st.warning("⚠️ Sheet does not have all 3 values (api_key, api_secret, access_token).")
        else:
            saved_api_key = tokens[0]
            saved_access_token = tokens[2]

            kite = KiteConnect(api_key=saved_api_key)
            kite.set_access_token(saved_access_token)

            if st.button("📈 Fetch BANKNIFTY Index Price"):
                try:
                    quote = kite.quote(["NSE:NIFTY BANK"])
                    last_price = quote["NSE:NIFTY BANK"]["last_price"]
                    st.success(f"💰 BANKNIFTY Index Price: {last_price}")
                except Exception as e:
                    st.error(f"❌ Failed to fetch BANKNIFTY price: {e}")
    except Exception as e:
        st.error(f"❌ Failed to read tokens from sheet: {e}")
else:
    st.warning("⚠️ Google Sheet not connected. Step 1 must succeed first.")
