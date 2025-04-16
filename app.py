import streamlit as st
from kiteconnect import KiteConnect
import datetime as dt
from tracker import get_all_returns, analyze_contribution

st.set_page_config(page_title="BANKNIFTY Tracker", layout="wide")
st.title("📊 BANKNIFTY Component Impact Tracker")

# Section 1: Token Generator
st.header("🔐 Zerodha Access Token Generator")

with st.expander("Generate Access Token", expanded=False):
    api_key = st.text_input("API Key")
    api_secret = st.text_input("API Secret", type="password")

    if api_key and api_secret:
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        st.markdown("1. Click to log in and get your `request_token`:")
        st.code(login_url)
        st.link_button("Login to Zerodha", login_url)

        request_token = st.text_input("Paste your request_token here")

        if request_token:
            try:
                session = kite.generate_session(request_token, api_secret=api_secret)
                access_token = session["access_token"]
                st.success("✅ Access token generated successfully!")
                st.code(access_token)
                st.markdown("Paste the below into Streamlit Secrets:")
                st.code(f"""toml
api_key = "{api_key}"
access_token = "{access_token}"
api_secret = "{api_secret}"
""", language="toml")
            except Exception as e:
                st.error(f"Error generating access token: {e}")

# Section 2: Analysis Tool
st.header("📈 BANKNIFTY Contribution Analysis")

col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
with col2:
    to_date = st.date_input("To Date", dt.date.today())

if st.button("Run Analysis"):
    st.info("🔄 Fetching data and analyzing...")
    try:
        df = get_all_returns(from_date, to_date)
        summary = analyze_contribution(df, as_text=True)
        st.success("✅ Analysis complete.")
        st.text_area("Regression Output", summary, height=400)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
