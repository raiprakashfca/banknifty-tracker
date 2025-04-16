import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Generator + Google Sheet Saver")

# --- SECTION 1: Google Sheet Setup ---
st.subheader("Step 1: Connect to Google Sheet")

sheet_ok = False
sheet = None

try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    sheet_ok = True
    st.success("✅ Connected to Google Sheet: `ZerodhaTokenStore`")
except Exception as e:
    st.error(f"❌ Could not connect to Google Sheets: {e}")

# --- SECTION 2: Zerodha Token Generation ---
st.subheader("Step 2: Generate Zerodha Access Token")

api_key = st.text_input("🔑 Enter API Key")
api_secret = st.text_input("🔒 Enter API Secret", type="password")

if api_key and api_secret:
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()
    st.markdown(f"🔗 [Click here to login to Zerodha and get request_token]({login_url})")

    request_token = st.text_input("📥 Paste request_token from URL")

    if request_token:
        try:
            session = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session["access_token"]
            st.success("✅ Access token generated!")
            st.code(access_token)

            # Save to Google Sheet
            if st.button("💾 Save to Google Sheet"):
                if not sheet_ok:
                    st.warning("⚠️ Google Sheet not connected.")
                else:
                    try:
                        sheet.update("A1", api_key)
                        sheet.update("B1", api_secret)
                        sheet.update("C1", access_token)
                        st.success("✅ Token saved to Google Sheet successfully!")
                    except Exception as e:
                        st.error(f"❌ Failed to save to sheet: {e}")

        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")
else:
    st.info("ℹ️ Please enter your API Key and Secret to begin.")
