import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from theme import apply_theme, plotly_layout, EMERALD, GOLD, SCALE_DIVERG

st.set_page_config(page_title="Alpha Forge Pro", layout="wide", page_icon="📈")
apply_theme()

st.markdown("""
<div style="display:flex; align-items:baseline; gap:12px; margin-bottom:0.2rem;">
  <span style="font-family:'DM Serif Display',serif; font-size:2.2rem;
               color:#F5F0E8; letter-spacing:0.01em;">Alpha Forge</span>
  <span style="font-family:'IBM Plex Mono',monospace; font-size:0.72rem;
               color:#00C896; letter-spacing:0.18em; text-transform:uppercase;
               border:1px solid rgba(0,200,150,0.35); padding:3px 9px;
               border-radius:2px; vertical-align:middle;">PRO</span>
</div>
<p style="font-family:'IBM Plex Sans',sans-serif; font-size:0.83rem;
          color:#6B7A94; margin-top:4px; margin-bottom:0; letter-spacing:0.03em;">
  Institutional Quantitative Portfolio Suite &nbsp;&middot;&nbsp;
  Configure your universe in the sidebar, then sync market data to begin.
</p>
<hr style="border-color:rgba(255,255,255,0.06); margin:1rem 0 1.6rem 0;">
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="padding:0.4rem 0 1rem 0; border-bottom:1px solid rgba(255,255,255,0.07);
            margin-bottom:1.1rem;">
  <div style="font-family:'DM Serif Display',serif; font-size:1.05rem;
              color:#C9A84C; letter-spacing:0.03em;">Universe Config</div>
  <div style="font-family:'IBM Plex Mono',monospace; font-size:0.60rem;
              color:#6B7A94; letter-spacing:0.14em; text-transform:uppercase;
              margin-top:3px;">Parameters &amp; Data Feed</div>
</div>
""", unsafe_allow_html=True)

ticker_list = st.sidebar.text_area(
    "Ticker Universe",
    "BSX, CBRE, CI, CRH, DIS, DY, EXE, FLEX, FN, FWONA, "
    "GWRE, ICE, MRVL, MTZ, NBIX, NDAQ, NOW, NVT, PANW, "
    "PLTR, PODD, SE, SFD, SPGI, SPXC, SSNC, TMO, TRU, TTMI, VST, YUMC"
)
tickers = [t.strip().upper() for t in ticker_list.split(',') if t.strip()]
start_date = st.sidebar.date_input("Analysis Start Date", pd.to_datetime("2024-01-01"))
benchmark = st.sidebar.text_input("Benchmark", "SPY")
st.sidebar.markdown("<div style='margin:0.8rem 0 0.4rem 0;'></div>", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_global_data(tks, bench, start):
    all_syms = list(set(tks + [bench, '^TNX']))
    data = yf.download(all_syms, start=start, auto_adjust=True, progress=False)['Close']
    data = data.dropna(axis=1, how='all')
    available_tks = [t for t in tks if t in data.columns]
    current_rf = float(data['^TNX'].iloc[-1] / 100) if '^TNX' in data.columns else 0.044
    returns = data.pct_change().dropna()
    return data, returns, current_rf, available_tks


if st.sidebar.button("Sync Market Data", type="primary"):
    with st.spinner("Fetching market data..."):
        try:
            raw, ret, rf, avail_tks = get_global_data(tickers, benchmark, str(start_date))
            st.session_state['raw_data'] = raw
            st.session_state['returns'] = ret
            st.session_state['rf'] = rf
            st.session_state['tickers'] = avail_tks
            st.session_state['benchmark'] = benchmark
            failed = [t for t in tickers if t not in avail_tks]
            if failed:
                st.warning(f"Could not load: {', '.join(failed)}")
            st.success(f"Universe synced — {len(avail_tks)} instruments loaded.")
        except Exception as e:
            st.error(f"Sync failed: {e}")

if 'returns' not in st.session_state:
    st.markdown("""
    <div style="margin-top:3rem; padding:2rem; background:#1A1F2E;
                border:1px solid rgba(255,255,255,0.07); border-radius:6px;
                border-left:3px solid #00C896; max-width:520px;">
      <div style="font-family:'DM Serif Display',serif; font-size:1.1rem;
                  color:#F5F0E8; margin-bottom:0.5rem;">Ready to initialise</div>
      <div style="font-family:'IBM Plex Sans',sans-serif; font-size:0.83rem;
                  color:#6B7A94; line-height:1.6;">
        Set your ticker universe and start date in the sidebar,
        then click <strong style="color:#00C896;">Sync Market Data</strong> to load prices.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

raw_data      = st.session_state['raw_data']
returns       = st.session_state['returns']
tickers       = st.session_state['tickers']
rf            = st.session_state['rf']
bench         = st.session_state['benchmark']
stock_returns = returns[tickers]

def section_label(text):
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.62rem;
                color:#6B7A94; letter-spacing:0.14em; text-transform:uppercase;
                margin-bottom:0.5rem; margin-top:1.6rem;">{text}</div>
    """, unsafe_allow_html=True)

section_label("Portfolio Universe Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Instruments", len(tickers))
col2.metric("Risk-Free Rate", f"{rf:.2%}")
col3.metric("Data From", str(returns.index[0].date()))
col4.metric("Trading Days", len(returns))

section_label("Risk / Return Summary")
ann_ret = (stock_returns.mean() * 252).rename("Ann. Return")
ann_vol = (stock_returns.std() * np.sqrt(252)).rename("Ann. Vol")
sharpe  = ((ann_ret - rf) / ann_vol).rename("Sharpe")
summary = pd.concat([ann_ret, ann_vol, sharpe], axis=1)
summary.index.name = "Ticker"

st.dataframe(
    summary.style.format({
        "Ann. Return": "{:.2%}",
        "Ann. Vol":    "{:.2%}",
        "Sharpe":      "{:.2f}",
    }).background_gradient(subset=["Sharpe"], cmap="RdYlGn"),
    use_container_width=True,
    height=420,
)

section_label("Asset Correlation Matrix")
corr = stock_returns.corr()
fig = px.imshow(
    corr,
    color_continuous_scale=[[0, "#FF5B5B"], [0.5, "#242938"], [1, "#00C896"]],
    zmin=-1, zmax=1,
    aspect="auto",
    text_auto=".2f",
)
fig.update_traces(textfont=dict(family="IBM Plex Mono, monospace", size=9))
fig.update_layout(**plotly_layout(
    title="Pairwise Pearson Correlation — Daily Returns",
    height=560,
    margin=dict(l=60, r=20, t=56, b=60),
    coloraxis_colorbar=dict(
        tickfont=dict(family="IBM Plex Mono, monospace", size=9),
        title=dict(text="rho", font=dict(family="IBM Plex Mono, monospace")),
        thickness=12, len=0.7,
    )
))
st.plotly_chart(fig, use_container_width=True)
