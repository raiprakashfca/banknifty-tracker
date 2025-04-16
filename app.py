import streamlit as st
from tracker import get_all_returns, analyze_contribution
import datetime as dt
import os

st.set_page_config(layout="wide")

st.title("📊 BANKNIFTY Component Tracker")

# Date Range
from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
to_date = st.date_input("To Date", dt.date.today())

# Run analysis
if st.button("Run Analysis"):
    st.write("🔁 Fetching and processing live data...")
    df = get_all_returns(from_date, to_date)
    
    st.write("✅ Data fetched. Running regression...")
    summary = analyze_contribution(df, as_text=True)

    st.text_area("Regression Summary", summary, height=400)
