import streamlit as st
import datetime as dt

st.set_page_config(layout="wide")
st.title("📊 BANKNIFTY Component Tracker")

# Try importing tracker safely
try:
    from tracker import get_all_returns, analyze_contribution
    connection_ok = True
except Exception as e:
    connection_ok = False
    st.error("❌ Unable to connect to Zerodha. Please check your access token.")
    st.caption(f"🔍 Details: {e}")

# Date selectors
from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
to_date = st.date_input("To Date", dt.date.today())

# Run Analysis
if st.button("Run Analysis"):
    if not connection_ok:
        st.warning("⚠️ Please regenerate your Zerodha token using `get_and_save_token.py`")
    else:
        st.write("🔁 Fetching and processing live data...")
        df = get_all_returns(from_date, to_date)

        st.write("✅ Data fetched. Running regression...")
        summary = analyze_contribution(df, as_text=True)

        st.text_area("📈 Regression Summary", summary, height=400)
