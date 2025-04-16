import gspread
from kiteconnect import KiteConnect
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import datetime as dt
import pandas as pd

# --- Authenticate with Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds = st.secrets["GOOGLE_SERVICE_ACCOUNT"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# --- Load API keys from Google Sheet ---
sheet = client.open("ZerodhaTokenStore").sheet1
tokens = sheet.row_values(1)  # Expecting: [api_key, api_secret, access_token]

api_key = tokens[0]
api_secret = tokens[1]
access_token = tokens[2]

# --- Setup KiteConnect ---
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# --- Function to fetch BANKNIFTY Index Price ---
def get_banknifty_price():
    quote = kite.quote(["NSE:NIFTY BANK"])
    return quote["NSE:NIFTY BANK"]["last_price"]

# --- Function to fetch historical OHLC (can be reused for any symbol) ---
def get_ohlc(symbol, interval, from_date, to_date):
    try:
        instrument_list = kite.instruments("NSE")
        token = next((item["instrument_token"] for item in instrument_list if item["tradingsymbol"] == symbol and item["exchange"] == "NSE"), None)
        if not token:
            raise Exception(f"Token not found for {symbol}")
        data = kite.historical_data(token, from_date, to_date, interval)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching OHLC for {symbol}: {e}")
        return pd.DataFrame()

# --- Dummy Analysis Example ---
def get_all_returns(from_date, to_date):
    price = get_banknifty_price()
    return [
        {"date": from_date, "price": price},
        {"date": to_date, "price": price + 100}
    ]

def analyze_contribution(df, as_text=False):
    if not df:
        return "⚠️ No data to analyze."
    return f"📊 BANKNIFTY moved from {df[0]['price']} to {df[1]['price']}."
