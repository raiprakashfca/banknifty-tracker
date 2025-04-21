import streamlit as st
from kiteconnect import KiteConnect
import datetime as dt
from tracker import get_all_returns, analyze_contribution
from token_utils import load_credentials_from_gsheet

st.set_page_config(page_title="BANKNIFTY Tracker", layout="wide")
st.title("📊 BANKNIFTY Component Impact Tracker")

# Load credentials from Google Sheets via shared utility
st.header("🔐 Loading Zerodha credentials from Google Sheets")

try:
    api_key, api_secret, access_token, valid_token = load_credentials_from_gsheet(st.secrets)

    if valid_token:
        st.success("✅ Access token is valid. Loaded from Google Sheet.")

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
    else:
        st.warning("⚠️ Access token from sheet is invalid. Please provide a new one.")

except Exception as e:
    st.error(f"🚨 Failed to load credentials from Google Sheets: {e}")
    valid_token = False

if not valid_token:
    st.header("🔑 Enter New Zerodha Access Token")
    api_key = st.text_input("API Key", value=api_key or "")
    api_secret = st.text_input("API Secret", type="password", value=api_secret or "")
    request_token = st.text_input("Paste request_token")

    if st.button("Generate New Access Token") and api_key and api_secret and request_token:
        try:
            kite = KiteConnect(api_key=api_key)
            session = kite.generate_session(request_token, api_secret=api_secret)
            access_token = session["access_token"]
            st.success("✅ New access token generated!")
            st.code(access_token)
            st.markdown("**Please update this token back into the Google Sheet manually.**")
        except Exception as e:
            st.error(f"❌ Failed to generate token: {e}")
