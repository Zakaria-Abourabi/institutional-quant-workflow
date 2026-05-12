import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Alpha Forge Pro", layout="wide", page_icon="🚀")

st.title("🚀 Alpha Forge: Institutional Quant Suite")
st.markdown("""
Welcome to the Pro Suite. Use the sidebar to configure your universe, 
and navigate through the tabs to perform deep-dive analytics.
""")

# --- GLOBAL SIDEBAR ---
st.sidebar.header("📡 Global Configuration")
ticker_list = st.sidebar.text_area("Ticker Universe", "AAPL, MSFT, NVDA, GOOG, AMZN, TSLA, PLTR, TLT, GLD")
tickers = [t.strip().upper() for t in ticker_list.split(',')]
start_date = st.sidebar.date_input("Analysis Start Date", pd.to_datetime("2023-01-01"))
benchmark = st.sidebar.text_input("Benchmark ETF", "SPY")

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_global_data(tks, bench, start):
    all_syms = list(set(tks + [bench, '^TNX']))
    data = yf.download(all_syms, start=start, auto_adjust=True)['Close']
    current_rf = data['^TNX'].iloc[-1] / 100
    returns = data.pct_change().dropna()
    return data, returns, current_rf

# Store in Session State so other pages can access it
if st.sidebar.button("Sync Market Data"):
    with st.spinner("Synchronizing..."):
        raw, ret, rf = get_global_data(tickers, benchmark, start_date)
        st.session_state['raw_data'] = raw
        st.session_state['returns'] = ret
        st.session_state['rf'] = rf
        st.session_state['tickers'] = tickers
        st.session_state['benchmark'] = benchmark
        st.success("Universe Synced!")

if 'returns' not in st.session_state:
    st.info("Please click 'Sync Market Data' in the sidebar to begin.")
    st.stop()