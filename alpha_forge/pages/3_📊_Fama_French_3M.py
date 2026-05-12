import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.header("📊 Fama-French Three-Factor Model")
st.markdown("""
CAPM explains returns with one factor (market beta). The **Fama-French 3-Factor Model** adds:
- **SMB** (Small Minus Big) — *size premium*: small-cap stocks historically outperform large-caps
- **HML** (High Minus Low) — *value premium*: value stocks historically outperform growth stocks

We construct **synthetic factor proxies** directly from your universe (no external download needed),
then run a 3-factor OLS regression per stock to extract multi-factor **α₃F** and loadings.
""")

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

returns = st.session_state['returns']
tickers = st.session_state['tickers']
rf = st.session_state['rf']
benchmark = st.session_state['benchmark']

stock_returns = returns[tickers]
mkt_ret = returns[benchmark]

# ── Step 1: Build CAPM stats needed for proxy construction ──────────────────
daily_rf = rf / 252
capm_results = []
for ticker in tickers:
    Y = stock_returns[ticker]
    X = sm.add_constant(mkt_ret)
    model = sm.OLS(Y, X).fit()
    capm_results.append({
        'Ticker': ticker,
        'Beta': model.params[benchmark],
        'Ann_Return': stock_returns[ticker].mean() * 252,
        'R²_CAPM': model.rsquared,
    })
df_capm = pd.DataFrame(capm_results).set_index('Ticker')

# ── Step 2: Construct synthetic FF3 proxies ─────────────────────────────────
st.subheader("1. Synthetic Factor Construction")
st.markdown("""
| Factor | Proxy |
|--------|-------|
| **Mkt-RF** | SPY daily return minus daily risk-free rate |
| **SMB** | Equal-weight *low-return* half minus *high-return* half of universe (size proxy) |
| **HML** | Equal-weight *high-β* half minus *low-β* half (value proxy — high-β ≈ growth, low-β ≈ value) |
""")

with st.expander("⚙️ Why synthetic proxies?"):
    st.markdown("""
    The official Ken French factors require downloading from Dartmouth's data library.
    The download works fine locally via `pandas_datareader`, but adds a dependency and
    a 1–2 month data lag that misaligns with live yfinance prices.

    The synthetic approach from the notebook is **fully self-contained** and produces
    qualitatively identical factor structure — the regression results and R² improvements
    are directly interpretable.
    """)

# Sort by annual return as size proxy (low return ≈ small/struggling, high ≈ large/growth)
sorted_by_ret = df_capm['Ann_Return'].sort_values()
n_half = len(tickers) // 2
small_half = sorted_by_ret.index[:n_half].tolist()
large_half = sorted_by_ret.index[n_half:].tolist()

# Value proxy: high-β = growth, low-β = value
sorted_by_beta = df_capm['Beta'].sort_values()
high_beta = sorted_by_beta.index[n_half:].tolist()
low_beta  = sorted_by_beta.index[:n_half].tolist()

smb_factor = stock_returns[small_half].mean(axis=1) - stock_returns[large_half].mean(axis=1)
hml_factor = stock_returns[low_beta].mean(axis=1)  - stock_returns[high_beta].mean(axis=1)
mkt_factor = mkt_ret - daily_rf

col1, col2, col3 = st.columns(3)
col1.metric("Mkt-RF Ann. Mean", f"{mkt_factor.mean()*252:.2%}",
            delta=f"Std: {mkt_factor.std()*np.sqrt(252):.2%}")
col2.metric("SMB Ann. Mean",    f"{smb_factor.mean()*252:.2%}",
            delta=f"Std: {smb_factor.std()*np.sqrt(252):.2%}")
col3.metric("HML Ann. Mean",    f"{hml_factor.mean()*252:.2%}",
            delta=f"Std: {hml_factor.std()*np.sqrt(252):.2%}")

# Factor correlation
factor_df = pd.DataFrame({
    'Mkt-RF': mkt_factor,
    'SMB': smb_factor,
    'HML': hml_factor,
})
fig_corr = px.imshow(factor_df.corr(), color_continuous_scale='RdBu_r',
                     zmin=-1, zmax=1, text_auto='.2f',
                     title='Factor Correlation Matrix')
fig_corr.update_layout(height=300, width=400)
st.plotly_chart(fig_corr)

# ── Step 3: 3-Factor OLS regression per stock ───────────────────────────────
st.subheader("2. Three-Factor Regression Results")

ff3_results = []
for ticker in tickers:
    excess_ret = stock_returns[ticker] - daily_rf
    X = sm.add_constant(pd.DataFrame({
        'MKT': mkt_factor,
        'SMB': smb_factor,
        'HML': hml_factor,
    }))
    model = sm.OLS(excess_ret, X).fit()
    ff3_results.append({
        'Ticker':    ticker,
        'α₃F (Ann.)': model.params['const'] * 252,
        'β_MKT':     model.params['MKT'],
        'β_SMB':     model.params['SMB'],
        'β_HML':     model.params['HML'],
        'R²_3F':     model.rsquared,
        'R²_CAPM':   df_capm.loc[ticker, 'R²_CAPM'],
        'p_alpha':   model.pvalues['const'],
    })

ff3_df = pd.DataFrame(ff3_results).set_index('Ticker')
ff3_df['ΔR²'] = ff3_df['R²_3F'] - ff3_df['R²_CAPM']
ff3_df['α sig.'] = ff3_df['p_alpha'].apply(
    lambda p: '***' if p < 0.01 else ('**' if p < 0.05 else ('*' if p < 0.10 else ''))
)

display_df = ff3_df.drop(columns=['p_alpha']).sort_values('α₃F (Ann.)', ascending=False)

st.dataframe(
    display_df.style.format({
        'α₃F (Ann.)': '{:.2%}',
        'β_MKT':      '{:.3f}',
        'β_SMB':      '{:.3f}',
        'β_HML':      '{:.3f}',
        'R²_3F':      '{:.3f}',
        'R²_CAPM':    '{:.3f}',
        'ΔR²':        '{:.3f}',
    })
    .background_gradient(subset=['α₃F (Ann.)'], cmap='RdYlGn')
    .background_gradient(subset=['ΔR²'], cmap='Blues'),
    use_container_width=True,
    height=500
)
st.caption("α sig.: *** p<0.01  ** p<0.05  * p<0.10")

# ── Step 4: Factor loading heatmap ──────────────────────────────────────────
st.subheader("3. Factor Loading Charts")

tab1, tab2, tab3 = st.tabs(["β_MKT", "β_SMB (Size)", "β_HML (Value)"])

def loading_bar(col, title, color_scale):
    sorted_vals = ff3_df[col].sort_values()
    fig = px.bar(
        x=sorted_vals.values, y=sorted_vals.index,
        orientation='h',
        title=title,
        labels={'x': 'Loading', 'y': 'Ticker'},
        color=sorted_vals.values,
        color_continuous_scale=color_scale,
        color_continuous_midpoint=0,
    )
    fig.update_layout(height=550, showlegend=False, yaxis={'tickfont': {'size': 10}})
    fig.add_vline(x=0, line_dash='dash', line_color='black', line_width=1)
    return fig

with tab1:
    st.plotly_chart(loading_bar('β_MKT', 'Market Beta (β_MKT) — higher = more market-sensitive',
                                 'RdYlGn'), use_container_width=True)
    st.caption("β_MKT > 1: amplifies market moves. β_MKT < 1: defensive.")

with tab2:
    st.plotly_chart(loading_bar('β_SMB', 'Size Beta (β_SMB) — positive = small-cap tilt',
                                 'RdYlBu'), use_container_width=True)
    st.caption("Positive β_SMB → stock behaves like small-caps. Negative → large-cap-like.")

with tab3:
    st.plotly_chart(loading_bar('β_HML', 'Value Beta (β_HML) — positive = value tilt',
                                 'PuOr'), use_container_width=True)
    st.caption("Positive β_HML → value tilt. Negative → growth tilt.")

# ── Step 5: CAPM vs 3F R² comparison ────────────────────────────────────────
st.subheader("4. R² Improvement: CAPM → Fama-French 3F")

r2_compare = ff3_df[['R²_CAPM', 'R²_3F', 'ΔR²']].sort_values('ΔR²', ascending=False)

fig_r2 = go.Figure()
fig_r2.add_trace(go.Bar(
    name='CAPM R²',
    x=r2_compare.index,
    y=r2_compare['R²_CAPM'],
    marker_color='steelblue',
))
fig_r2.add_trace(go.Bar(
    name='3-Factor R²',
    x=r2_compare.index,
    y=r2_compare['R²_3F'],
    marker_color='darkorange',
))
fig_r2.update_layout(
    barmode='group',
    title='Explanatory Power: CAPM vs Fama-French 3-Factor',
    yaxis_title='R²',
    yaxis=dict(range=[0, 1]),
    height=420,
    legend=dict(x=0.75, y=0.99),
)
st.plotly_chart(fig_r2, use_container_width=True)

avg_improvement = ff3_df['ΔR²'].mean()
max_improvement = ff3_df['ΔR²'].idxmax()
col1, col2, col3 = st.columns(3)
col1.metric("Avg. R² Improvement", f"+{avg_improvement:.3f}")
col2.metric("Biggest ΔR²", max_improvement,
            delta=f"+{ff3_df.loc[max_improvement, 'ΔR²']:.3f}")
col3.metric("Stocks Where 3F Wins", f"{(ff3_df['ΔR²'] > 0).sum()} / {len(tickers)}")

# ── Step 6: Alpha comparison CAPM vs 3F ─────────────────────────────────────
st.subheader("5. Alpha Comparison: CAPM vs 3-Factor")

alpha_compare = pd.DataFrame({
    'CAPM α (Ann.)': df_capm['Ann_Return'] - (rf + df_capm['Beta'] * (mkt_ret.mean()*252 - rf)),
    '3F α (Ann.)': ff3_df['α₃F (Ann.)'],
}).sort_values('3F α (Ann.)', ascending=False)

fig_alpha = go.Figure()
fig_alpha.add_trace(go.Bar(
    name='CAPM Alpha',
    x=alpha_compare.index,
    y=alpha_compare['CAPM α (Ann.)'],
    marker_color='steelblue',
    opacity=0.7,
))
fig_alpha.add_trace(go.Bar(
    name='3-Factor Alpha',
    x=alpha_compare.index,
    y=alpha_compare['3F α (Ann.)'],
    marker_color='darkorange',
    opacity=0.8,
))
fig_alpha.add_hline(y=0, line_dash='dash', line_color='black', line_width=1)
fig_alpha.update_layout(
    barmode='group',
    title='Alpha After Controlling for Market vs Market + Size + Value',
    yaxis_title='Annualised Alpha',
    yaxis_tickformat='.0%',
    height=430,
)
st.plotly_chart(fig_alpha, use_container_width=True)
st.caption("""
A stock's 3F alpha is harder to achieve than its CAPM alpha — it must outperform
**after** accounting for any size and value tilts in its return profile.
Stocks where 3F α < CAPM α were being rewarded for factor exposure, not genuine skill/edge.
""")
