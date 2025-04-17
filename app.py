import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd
import datetime as dt
import statsmodels.api as sm
import io
import time

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

# --- Step 3: Live Market Prices ---
st.subheader("📡 Live Market Prices (Click button to refresh)")

if st.button("🔄 Refresh Live Prices"):
    try:
        tokens = sheet.row_values(1)
        saved_api_key = tokens[0]
        saved_access_token = tokens[2]
        kite = KiteConnect(api_key=saved_api_key)
        kite.set_access_token(saved_access_token)

        live_symbols = ["NSE:NIFTY BANK", "NSE:HDFCBANK", "NSE:ICICIBANK", "NSE:SBIN", "NSE:AXISBANK", "NSE:KOTAKBANK", "NSE:BANKBARODA", "NSE:PNB"]
        live_data = kite.quote(live_symbols)

        live_table = []
        for s in live_symbols:
            name = s.split(":")[1]
            price = round(live_data[s]["last_price"], 2)
            prev_close = round(live_data[s].get("ohlc", {}).get("close", 0.0), 2)
            change = round(price - prev_close, 2)
            pct_change = round((change / prev_close * 100), 2) if prev_close else 0.0
            live_table.append({
                "Symbol": name,
                "Last Price": f"{price:.2f}",
                "Change": f"{change:+.2f}",
                "% Change": f"{pct_change:+.2f}%"
            })

        df_live = pd.DataFrame(live_table)
        def highlight_change(val):
            if isinstance(val, str) and val.startswith('+'):
                return 'color: green;'
            elif isinstance(val, str) and val.startswith('-'):
                return 'color: red;'
            return ''

        st.dataframe(df_live.style.applymap(highlight_change, subset=["Change", "% Change"]))
    except Exception as e:
        st.error(f"❌ Failed to fetch live prices: {e}")
