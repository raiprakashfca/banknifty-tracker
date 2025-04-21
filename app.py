import streamlit as st
from kiteconnect import KiteConnect
import pandas as pd
import statsmodels.api as sm
from tracker import get_all_returns
from token_utils import load_credentials_from_gsheet
import datetime as dt
import time

st.set_page_config(page_title="BANKNIFTY Impact Tracker", layout="wide")
st.title("📊 BANKNIFTY Component Impact Tracker")

# Load credentials
try:
    api_key, api_secret, access_token, valid_token = load_credentials_from_gsheet(st.secrets, sheet_name="Sheet1")
    if not valid_token:
        st.error("Invalid or missing access token.")
        st.stop()
except Exception as e:
    st.error(f"Failed to load credentials: {e}")
    st.stop()

# Inputs
from_date = st.date_input("From Date", dt.date.today() - dt.timedelta(days=30))
to_date = st.date_input("To Date", dt.date.today())
refresh_rate = st.slider("🔁 Refresh LTP every (seconds)", min_value=5, max_value=60, value=10)

run_analysis = st.button("Run Contribution Analysis")

if run_analysis:
    try:
        df = get_all_returns(api_key, access_token, from_date, to_date)

        if df.empty or "BANKNIFTY" not in df.columns:
            st.error("❌ Dataframe is empty or missing BANKNIFTY column.")
            st.stop()

        X = df[[col for col in df.columns if col not in ["date", "BANKNIFTY"]]]
        y = df["BANKNIFTY"]
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        coefs = model.params.drop("const")
        contrib_pct = 100 * coefs / coefs.sum()

        symbols = {
            "BANKNIFTY": "NSE:NIFTY BANK",
            "HDFCBANK": "NSE:HDFCBANK",
            "ICICIBANK": "NSE:ICICIBANK",
            "SBIN": "NSE:SBIN",
            "KOTAKBANK": "NSE:KOTAKBANK",
            "AXISBANK": "NSE:AXISBANK",
            "BANKBARODA": "NSE:BANKBARODA",
            "PNB": "NSE:PNB",
        }

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        placeholder = st.empty()

        while True:
            try:
                ltp_data = kite.ltp(list(symbols.values()))
                ltp = {stock: ltp_data[symbols[stock]]['last_price'] for stock in symbols if symbols[stock] in ltp_data}

                result_df = pd.DataFrame({
                    "Stock": coefs.index,
                    "LTP": [ltp.get(stock, "-") for stock in coefs.index],
                    "Contribution (%)": contrib_pct.values
                })

                banknifty_row = pd.DataFrame({
                    "Stock": ["BANKNIFTY"],
                    "LTP": [ltp.get("BANKNIFTY", "-")],
                    "Contribution (%)": [100.0]
                })

                final_df = pd.concat([banknifty_row, result_df.sort_values("Contribution (%)", ascending=False)], ignore_index=True)

                with placeholder.container():
                    st.subheader("📋 Contribution Summary (Live)")
                    st.dataframe(final_df.style.format({"Contribution (%)": "{:.2f}%", "LTP": "₹{:.2f}"}))

                time.sleep(refresh_rate)

            except Exception as live_error:
                st.error(f"⚠️ Live data fetch error: {live_error}")
                break

    except Exception as e:
        st.error(f"❌ Analysis failed: {e}")
