import streamlit as st
from kiteconnect import KiteConnect
import datetime as dt
import pandas as pd
from tracker import get_all_returns, analyze_contribution
from token_utils import load_credentials_from_gsheet
import statsmodels.api as sm
import threading

st.set_page_config(page_title="BANKNIFTY Tracker", layout="wide")
st.title("📊 BANKNIFTY Component Impact Tracker")

# Load credentials from Google Sheets via shared utility
st.header("🔐 Loading Zerodha credentials from Google Sheets")

live_prices = {}
start_prices = {}
coefs = None

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

                st.subheader("🔍 Contribution (%) of each stock to BANKNIFTY movement")
                if df.empty or "BANKNIFTY" not in df.columns:
                    st.error("❌ Dataframe is empty or missing BANKNIFTY column.")
                else:
                    X = df[[col for col in df.columns if col != "date" and col != "BANKNIFTY"]]
                    y = df["BANKNIFTY"]
                    X = sm.add_constant(X)
                    model = sm.OLS(y, X).fit()
                    coefs = model.params.drop("const")
                    contrib_pct = 100 * coefs / coefs.sum()
                    result_df = pd.DataFrame({
                        "Stock": coefs.index,
                        "Beta Coefficient": coefs.values,
                        "Contribution (%)": contrib_pct.values
                    })
                    st.dataframe(result_df.sort_values("Contribution (%)", ascending=False).reset_index(drop=True))

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

        # Live market tracker
        st.header("📡 Live Market Contribution Tracker (Experimental)")
        start_live = st.checkbox("Start Live Tracking")

        if start_live and coefs is not None:
            from kiteconnect import KiteTicker

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

            ltp = kite.ltp(list(symbols.values()))
            for s, d in symbols.items():
                start_prices[s] = ltp[d]["last_price"]

            kws = KiteTicker(api_key, access_token)

            def on_ticks(ws, ticks):
                for tick in ticks:
                    for s, d in symbols.items():
                        if tick["instrument_token"] == ltp[d]["instrument_token"]:
                            live_prices[s] = tick["last_price"]

            def on_connect(ws, response):
                tokens = [ltp[d]["instrument_token"] for d in symbols.values()]
                ws.subscribe(tokens)

            def run_websocket():
                kws.on_ticks = on_ticks
                kws.on_connect = on_connect
                kws.connect(threaded=True)

            threading.Thread(target=run_websocket).start()

            if live_prices:
                st.subheader("🔄 Live Contribution (based on real-time returns)")
                live_returns = {
                    s: (live_prices[s] - start_prices[s]) / start_prices[s]
                    for s in live_prices if s in start_prices
                }
                contrib_live = {
                    s: live_returns[s] * coefs.get(s, 0)
                    for s in live_returns
                }
                df_live = pd.DataFrame({
                    "Stock": list(contrib_live.keys()),
                    "Live Return": [round(v * 100, 2) for v in live_returns.values()],
                    "Live Impact": [round(v * 100, 2) for v in contrib_live.values()]
                }).sort_values("Live Impact", ascending=False)
                st.dataframe(df_live.reset_index(drop=True))

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
