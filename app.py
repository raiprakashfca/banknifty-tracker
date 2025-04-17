import streamlit as st
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd
import datetime as dt
import statsmodels.api as sm
import io

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
st.subheader("📡 Live Market Prices")

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
        price = live_data[s]["last_price"]
        change = live_data[s]["change"] if "change" in live_data[s] else 0.0
        change_color = "green" if change >= 0 else "red"
        live_table.append({"Symbol": name, "Last Price": price, "Change": f"{change:+.2f}"})

    df_live = pd.DataFrame(live_table)
    def highlight_change(val):
        if isinstance(val, str) and val.startswith('+'):
            return 'color: green;'
        elif isinstance(val, str) and val.startswith('-'):
            return 'color: red;'
        return ''

    st.dataframe(df_live.style.applymap(highlight_change, subset=["Change"]))
except Exception as e:
    st.error(f"❌ Failed to fetch live prices: {e}")

# --- Step 4: Historical OHLC + Regression Analysis ---
st.subheader("4️⃣ Historical OHLC + Regression Impact Report")

with st.expander("📅 Select Date Range and Interval"):
    start_date = st.date_input("Start Date", value=dt.date.today() - dt.timedelta(days=30))
    end_date = st.date_input("End Date", value=dt.date.today())
    interval = st.selectbox("Interval", ["day", "5minute", "15minute", "30minute", "60minute"])

if st.button("📊 Run Analysis"):
    try:
        symbols = ["BANKNIFTY", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BANKBARODA", "PNB"]
        ohlc_data = {}
        instruments = kite.instruments("NSE")

        for symbol in symbols:
            if symbol == "BANKNIFTY":
                token = 260105  # Hardcoded token for BANKNIFTY index
            else:
                token = next((i["instrument_token"] for i in instruments if i["tradingsymbol"] == symbol), None)
            if not token:
                st.warning(f"⚠️ Instrument token not found for {symbol}")
                continue
            data = kite.historical_data(token, start_date, end_date, interval)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            df.set_index("date", inplace=True)
            ohlc_data[symbol] = df["close"]

        df_combined = pd.DataFrame(ohlc_data)
        returns = df_combined.pct_change().dropna()

        st.subheader("📈 Component Impact on BANKNIFTY")
        X = returns[symbols[1:]]
        y = returns["BANKNIFTY"]
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        summary_df = pd.DataFrame({
            "Stock": X.columns[1:],
            "Impact (Beta)": model.params[1:],
            "P-value": model.pvalues[1:]
        }).sort_values("Impact (Beta)", ascending=False)

        st.dataframe(summary_df, use_container_width=True)

        with st.expander("📘 What Do These Numbers Mean?"):
            st.markdown("""
            - **Impact (Beta)**: Shows how much BANKNIFTY is expected to move when the stock moves.
              - Example: If HDFCBANK has Beta = 0.45, a 1% rise in HDFCBANK contributes ~0.45% to BANKNIFTY.
            - **P-value**: Indicates confidence in that relationship.
              - P < 0.05 = statistically significant (reliable)
              - P > 0.1 = could be random noise
            """)

        # --- Export to Excel ---
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_combined.to_excel(writer, sheet_name='Prices')
            returns.to_excel(writer, sheet_name='Returns')
            summary_df.to_excel(writer, sheet_name='ImpactReport', index=False)
        st.download_button("📥 Download Excel Report", data=excel_buffer.getvalue(), file_name="banknifty_analysis.xlsx")

    except Exception as e:
        st.error(f"❌ Analysis failed: {e}")
