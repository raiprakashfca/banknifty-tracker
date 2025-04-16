import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Generator + Google Sheet Saver")

# --- Session State Setup ---
for key in ["kite", "api_key", "api_secret", "access_token", "login_url", "request_token"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- Google Sheet Setup ---
try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    sheet_ok = True
    st.success("✅ Connected to Google Sheet")
except Exception as e:
    sheet_ok = False
    st.error(f"❌ Could not connect to Google Sheets: {e}")

# --- API Key + Secret Input ---
st.subheader("Step 1: Enter Zerodha API Key & Secret")
st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key or "")
st.session_state.api_secret = st.text_input("API Secret", value=st.session_state.api_secret or "", type="password")

# --- Generate Login URL ---
if st.button("🔗 Generate Zerodha Login URL"):
    st.session_state.kite = KiteConnect(api_key=st.session_state.api_key)
    st.session_state.login_url = st.session_state.kite.login_url()

# Show Login URL if generated
if st.session_state.login_url:
    st.markdown(f"🔗 [Click here to login and get request_token]({st.session_state.login_url})")

# --- Step 2: Paste request_token ---
st.subheader("Step 2: Paste `request_token` and generate Access Token")
st.session_state.request_token = st.text_input("📥 Paste request_token")

# ✅ Always show this button now
if st.button("⚡ Generate Access Token"):
    if st.session_state.kite and st.session_state.request_token:
        try:
            session = st.session_state.kite.generate_session(
                st.session_state.request_token,
                st.session_state.api_secret
            )
            st.session_state.access_token = session["access_token"]
            st.success("✅ Access token generated successfully!")
            st.code(st.session_state.access_token)
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")
    else:
        st.warning("⚠️ Please ensure both login link and request_token are available.")

# --- Step 3: Save to Google Sheet ---
if st.session_state.access_token:
    st.subheader("Step 3: Save to Google Sheet")
    if st.button("💾 Save token to Google Sheet"):
        try:
            sheet.update("A1", st.session_state.api_key)
            sheet.update("B1", st.session_state.api_secret)
            sheet.update("C1", st.session_state.access_token)
            st.success("✅ Token saved to Google Sheet successfully!")
        except Exception as e:
            st.error(f"❌ Failed to save token: {e}")
