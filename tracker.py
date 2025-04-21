import streamlit as st
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import statsmodels.api as sm

# Load credentials from Streamlit secrets
try:
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

# Authenticate with Kite API
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Define BANKNIFTY and components
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

# Fetch instrument token
def get_token(symbol):
    try:
        instrument = symbols[symbol]
        return kite.ltp([instrument])[instrument]["instrument_token"]
    except Exception as e:
        st.error(f"Failed to fetch instrument token for {symbol}: {e}")
        st.stop()

# Fetch historical data
def get_data(symbol, from_date, to_date, interval="day"):
    token = get_token(symbol)
    data = kite.historical_data(token, from_date, to_date, interval)
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df

# Calculate returns
def calculate_returns(df):
    df = df.sort_values("date")
    df["return"] = df["close"].pct_change()
    return df[["date", "return"]]

# Combine returns from all symbols
def get_all_returns(from_date, to_date):
    returns_df = pd.DataFrame()
    for symbol in symbols:
        df = get_data(symbol, from_date, to_date)
        df = calculate_returns(df)
        df.rename(columns={"return": symbol}, inplace=True)
        if returns_df.empty:
            returns_df = df
        else:
            returns_df = pd.merge(returns_df, df[["date", symbol]], on="date", how="outer")
    return returns_df.dropna()

# Analyze contribution using regression
def analyze_contribution(returns_df, as_text=False):
    X = returns_df[[s for s in symbols if s != "BANKNIFTY"]]
    y = returns_df["BANKNIFTY"]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    if as_text:
        return model.summary().as_text()
    return model
