import streamlit as st
from kiteconnect import KiteConnect

# ✅ Streamlit Cloud reads secrets from app settings
api_key = st.secrets["api_key"]
access_token = st.secrets["access_token"]

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Example usage: fetch BANKNIFTY token
def get_banknifty_token():
    instruments = kite.instruments("NSE")
    for instrument in instruments:
        if instrument["tradingsymbol"] == "BANKNIFTY" and instrument["segment"] == "NSE-INDEX":
