import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Generator + Google Sheet Saver")

# --- Session State ---
if "kite" not in st.session_state:
    st.session_state.kite = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_secret" not in st.session_state:
    st.session_state.api_secret = ""
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "login_url" not in st.session_state:
    st.session_state.login_url = None

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
    sheet = None
    sheet_ok = False
    st.error(f"❌ Could not connect to Google Sheets: {e}")

# --- Step 1: API Input ---
st.subheader("Step 1: Enter Zerodha API Key and Secret")
st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key)
st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret, type="password")

# --- Step 2: Generate Login URL ---
if st.button("🔗 Generate Zerodha Login URL"):
    st.session_state.kite = KiteConnect(api_key=st.session_state.api_key)
    st.session_state.login_url = st.session_state.kite.login_url()

if st.session_state.login_url:
    st.markdown(f"[Click here to login to Zerodha and get `request_token`]({st.session_state.login_url})")

# --- Step 3: Paste Request Token ---
request_token = st.text_input("📥 Paste request_token from URL")

if request_token and st.session_state.kite:
    if st.session_state.access_token is None:
        try:
            session = st.session_state.kite.generate_session(request_token, st.session_state.api_secret)
            st.session_state.access_token = session["access_token"]
            st.success("✅ Access token generated successfully!")
            st.code(st.session_state.access_token)
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")

# --- Step 4: Save to Google Sheet ---
if st.session_state.access_token:
    if st.button("💾 Save token to Google Sheet"):
        if sheet_ok:
            try:
                sheet.update("A1", st.session_state.api_key)
                sheet.update("B1", st.session_state.api_secret)
                sheet.update("C1", st.session_state.access_token)
                st.success("✅ Token saved to Google Sheet successfully!")
            except Exception as e:
                st.error(f"❌ Failed to update sheet: {e}")
        else:
            st.error("❌ Google Sheet connection not available.")
