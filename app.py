import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Manager + BANKNIFTY Tracker")

# --- Step 1: Connect to Google Sheet ---
st.subheader("1️⃣ Connect to Google Sheet")

try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").worksheet("Sheet1")
    st.success("✅ Connected to Google Sheet successfully.")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {e}")
    st.stop()

# --- Step 2: API Key Input and Login URL ---
st.subheader("2️⃣ Enter API Credentials")

api_key = st.text_input("🔑 API Key", value=st.session_state.get("api_key", ""))
api_secret = st.text_input("🔒 API Secret", type="password", value=st.session_state.get("api_secret", ""))

if api_key and api_secret:
    try:
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        st.markdown(f"🔗 [Login to Zerodha → get `request_token`]({login_url})")
    except Exception as e:
        st.error(f"❌ Failed to create login URL: {e}")
        st.stop()

    request_token = st.text_input("📥 Paste request_token from redirected URL")

    if request_token and st.button("🔓 Generate Access Token"):
        try:
            session = kite.generate_session(request_token, api_secret=api_secret)
            st.session_state["access_token"] = session["access_token"]
            st.session_state["api_key"] = api_key
            st.session_state["api_secret"] = api_secret
            st.success("✅ Access token generated successfully!")
            st.code(st.session_state["access_token"])
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")

# --- Save to Google Sheet Button ---
if "access_token" in st.session_state and st.button("💾 Save to Google Sheet"):
    try:
        sheet.update("A1", [[
            st.session_state["api_key"],
            st.session_state["api_secret"],
            st.session_state["access_token"]
        ]])
        st.success("✅ Token saved to Google Sheet (A1:C1)")
    except Exception as e:
        st.error(f"❌ Failed to write to Google Sheet: {e}")

# --- Step 3: Use Saved Token to Fetch BANKNIFTY Price ---
st.subheader("3️⃣ Test Saved Token - BANKNIFTY Price")

if st.button("📈 Fetch BANKNIFTY Index Price"):
    try:
        tokens = sheet.row_values(1)
        if len(tokens) < 3:
            st.warning("⚠️ Sheet does not contain all 3 values (API Key, Secret, Access Token)")
        else:
            saved_api_key = tokens[0]
            saved_access_token = tokens[2]

            kite = KiteConnect(api_key=saved_api_key)
            kite.set_access_token(saved_access_token)
            quote = kite.quote(["NSE:NIFTY BANK"])
            last_price = quote["NSE:NIFTY BANK"]["last_price"]
            st.success(f"💰 BANKNIFTY Index Spot Price: {last_price}")
    except Exception as e:
        st.error(f"❌ Failed to fetch BANKNIFTY price: {e}")
