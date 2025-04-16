import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(layout="wide")
st.title("🔐 Zerodha Token Generator + Sheet Saver")

# --- Connect to Google Sheet ---
st.subheader("1️⃣ Connect to Google Sheet")

try:
    google_creds = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
    client = gspread.authorize(creds)
    sheet = client.open("ZerodhaTokenStore").sheet1
    st.success("✅ Connected to Google Sheet successfully.")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {e}")
    st.stop()

# --- API Inputs ---
st.subheader("2️⃣ Enter API Credentials")

api_key = st.text_input("🔑 API Key", key="api_key_input")
api_secret = st.text_input("🔒 API Secret", type="password", key="api_secret_input")

# Generate login URL
if api_key and api_secret:
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()
    st.markdown(f"🔗 [Login to Zerodha → get `request_token`]({login_url})")
    request_token = st.text_input("📥 Paste request_token from URL")

    # --- Generate access token ---
    if request_token:
        try:
            session = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session["access_token"]
            st.success("✅ Access token generated successfully!")
            st.code(access_token)

            # --- Save to Google Sheet ---
            if st.button("💾 Save to Google Sheet"):
                try:
                    sheet.values_update(
                        "A1:C1",
                        params={"valueInputOption": "RAW"},
                        body={"values": [[api_key, api_secret, access_token]]}
                    )
                    st.success("✅ Credentials saved to Google Sheet (A1:C1)")
                except Exception as e:
                    st.error(f"❌ Failed to write to Google Sheet: {e}")
        except Exception as e:
            st.error(f"❌ Token generation failed: {e}")
else:
    st.info("ℹ️ Enter your Zerodha API Key and Secret to begin.")

# --- Use saved token to get BANKNIFTY price ---
st.subheader("3️⃣ Test Token from Sheet")

if st.button("📈 Fetch BANKNIFTY Index Price"):
    try:
        tokens = sheet.row_values(1)
        if len(tokens) < 3:
            st.warning("⚠️ Sheet does not have full credentials in A1:C1")
        else:
            saved_key = tokens[0]
            saved_token = tokens[2]

            kite = KiteConnect(api_key=saved_key)
            kite.set_access_token(saved_token)
            quote = kite.quote(["NSE:NIFTY BANK"])
            price = quote["NSE:NIFTY BANK"]["last_price"]
            st.success(f"✅ BANKNIFTY Index Spot: {price}")
    except Exception as e:
        st.error(f"❌ Failed to fetch BANKNIFTY: {e}")
