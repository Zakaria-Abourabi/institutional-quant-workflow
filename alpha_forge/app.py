import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Alpha Forge Pro", layout="wide", page_icon="🚀")

st.title("🚀 Alpha Forge: Institutional Quant Suite")
st.markdown("""
Welcome to the Pro Suite. Use the sidebar to configure your universe,
then click **Sync Market Data** before navigating to any tab.
""")

# --- GLOBAL SIDEBAR ---
st.sidebar.header("📡 Global Configuration")
ticker_list = st.sidebar.text_area(
    "Ticker Universe",
    "BSX, CBRE, CI, CRH, DIS, DY, EXE, FLEX, FN, FWONA, "
    "GWRE, ICE, MRVL, MTZ, NBIX, NDAQ, NOW, NVT, PANW, "
    "PLTR, PODD, SE, SFD, SPGI, SPXC, SSNC, TMO, TRU, TTMI, VST, YUMC"
)
tickers = [t.strip().upper() for t in ticker_list.split(',') if t.strip()]
start_date = st.sidebar.date_input("Analysis Start Date", pd.to_datetime("2024-01-01"))
benchmark = st.sidebar.text_input("Benchmark ETF", "SPY")


@st.cache_data(ttl=3600)
def get_global_data(tks, bench, start):
    all_syms = list(set(tks + [bench, '^TNX']))
    data = yf.download(all_syms, start=start, auto_adjust=True, progress=False)['Close']
    # Drop any symbols that failed to download
    data = data.dropna(axis=1, how='all')
    available_tks = [t for t in tks if t in data.columns]
    current_rf = float(data['^TNX'].iloc[-1] / 100) if '^TNX' in data.columns else 0.044
    returns = data.pct_change().dropna()
    return data, returns, current_rf, available_tks


if st.sidebar.button("🔄 Sync Market Data"):
    with st.spinner("Synchronizing market data..."):
        try:
            raw, ret, rf, avail_tks = get_global_data(tickers, benchmark, str(start_date))
            st.session_state['raw_data'] = raw
            st.session_state['returns'] = ret
            st.session_state['rf'] = rf
            st.session_state['tickers'] = avail_tks
            st.session_state['benchmark'] = benchmark
            failed = [t for t in tickers if t not in avail_tks]
            if failed:
                st.warning(f"Could not download: {', '.join(failed)}. Proceeding with available tickers.")
            st.success(f"✅ Universe synced! {len(avail_tks)} tickers loaded.")
        except Exception as e:
            st.error(f"Data sync failed: {e}")

if 'returns' not in st.session_state:
    st.info("👆 Please click **Sync Market Data** in the sidebar to begin.")
    st.stop()

# --- DASHBOARD OVERVIEW ---
raw_data = st.session_state['raw_data']
returns = st.session_state['returns']
tickers = st.session_state['tickers']
rf = st.session_state['rf']
bench = st.session_state['benchmark']

st.subheader("📊 Portfolio Universe Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tickers Loaded", len(tickers))
col2.metric("Risk-Free Rate", f"{rf:.2%}")
col3.metric("Data Since", str(returns.index[0].date()))
col4.metric("Trading Days", len(returns))

import numpy as np

# Quick stats table
stock_returns = returns[tickers]
ann_ret = (stock_returns.mean() * 252).rename("Ann. Return")
ann_vol = (stock_returns.std() * np.sqrt(252)).rename("Ann. Vol")
sharpe = ((ann_ret - rf) / ann_vol).rename("Sharpe")
summary = pd.concat([ann_ret, ann_vol, sharpe], axis=1)
summary.index.name = "Ticker"

st.dataframe(
    summary.style.format({
        "Ann. Return": "{:.2%}",
        "Ann. Vol": "{:.2%}",
        "Sharpe": "{:.2f}"
    }).background_gradient(subset=["Sharpe"], cmap="RdYlGn"),
    use_container_width=True,
    height=400
)

# Correlation heatmap
import plotly.express as px
corr = stock_returns.corr()
fig = px.imshow(corr, color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                title="Asset Correlation Matrix", aspect="auto")
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)
