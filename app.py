import streamlit as st
import datetime as dt
import os

st.set_page_config(layout="wide")
st.title("📊 BANKNIFTY Component Tracker")

# Try importing tracker logic
try:
    from tracker import get_all_returns, analyze_contribution
    connection_ok = True
except Exception as e:
    connection_ok = False
    st.error(f"❌ Could not load tracker module due to token error: {e}")

# Date Inputs
from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
to_date = st.date_input("To Date", dt.date.today())

# Button: Run Analysis
if st.button("Run Analysis"):
    if not connection_ok:
        st.warning("⚠️ Unable to connect to Zerodha. Please check if your access token is valid.")
    else:
        st.write("🔁 Fetching and processing live data...")
        df = get_all_returns(from_date, to_date)

        st.write("✅ Data fetched. Running regression...")
        summary = analyze_contribution(df, as_text=True)

        st.text_area("📈 Regression Summary", summary, height=400)
