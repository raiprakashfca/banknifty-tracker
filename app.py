import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Generator + Google Sheet Saver")

# --- SESSION STATE ---
if "kite" not in st.session_state:
    st.session_state.kite = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_secret" not in st.session_state:
    st.session_state.api_secret = ""
if "token_saved" not in st.session_state:
    st.session_state.token_saved = False

# --- Google Sheet Connection ---
try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    sheet_ok = True
    st.success("✅ Connected to Google Sheet: ZerodhaTokenStore")
except Exception as e:
    sheet_ok = False
    st.error(f"❌ Could not connect to Google Sheets: {e}")

# --- API Credentials Input ---
st.subheader("Step 1: Enter Zerodha API Key and Secret")
st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key)
st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret, type="password")

if st.session_state.api_key and st.session_state.api_secret:
    if st.button("🔗 Generate Login URL"):
        st.session_state.kite = KiteConnect(api_key=st.session_state.api_key)
        st.session_state.login_url = st.session_state.kite.login_url()
        st.success("✅ Login URL generated. Use it below.")
        st.markdown(f"[Click here to log in to Zerodha and get your `request_token`]({st.session_state.login_url})")

# --- Step 2: Paste Request Token ---
if "kite" in st.session_state and st.session_state.kite:
    st.subheader("Step 2: Paste `request_token` from redirect URL")
    request_token = st.text_input("Paste request_token from URL")

    if request_token:
        try:
            session = st.session_state.kite.generate_session(request_token, st.session_state.api_secret)
            access_token = session["access_token"]
            st.success("✅ Access token generated successfully!")
            st.code(access_token)

            if st.button("💾 Save to Google Sheet"):
                if sheet_ok:
                    sheet.update("A1", st.session_state.api_key)
                    sheet.update("B1", st.session_state.api_secret)
                    sheet.update("C1", access_token)
                    st.session_state.token_saved = True
                    st.success("✅ Token saved to Google Sheet successfully!")
                else:
                    st.error("❌ Cannot save to sheet. Connection failed.")
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")
