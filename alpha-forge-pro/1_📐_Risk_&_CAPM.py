import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.express as px
import plotly.graph_objects as go

st.header("📐 Risk & CAPM Analysis")

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

returns = st.session_state['returns']
tickers = st.session_state['tickers']
rf = st.session_state['rf']
benchmark = st.session_state['benchmark']

stock_returns = returns[tickers]
market_returns = returns[benchmark]

# --- OLS CAPM Regression ---
st.subheader("1. CAPM: Beta & Alpha (OLS Regression)")

results = []
for ticker in tickers:
    Y = stock_returns[ticker]
    X = sm.add_constant(market_returns)
    model = sm.OLS(Y, X).fit()
    results.append({
        'Ticker': ticker,
        'Beta': model.params[benchmark],
        'Daily Alpha': model.params['const'],
        'Ann. Alpha': model.params['const'] * 252,
        'Ann. Return': stock_returns[ticker].mean() * 252,
        'R²': model.rsquared,
    })

df_capm = pd.DataFrame(results).set_index('Ticker').sort_values('Beta', ascending=False)

st.dataframe(
    df_capm.style.format({
        'Beta': '{:.3f}',
        'Daily Alpha': '{:.4f}',
        'Ann. Alpha': '{:.2%}',
        'Ann. Return': '{:.2%}',
        'R²': '{:.3f}',
    }).background_gradient(subset=['Beta'], cmap='coolwarm')
    .background_gradient(subset=['Ann. Alpha'], cmap='RdYlGn'),
    use_container_width=True,
    height=500
)

# --- Security Market Line ---
st.subheader("2. Security Market Line (SML)")

market_excess_return = market_returns.mean() * 252 - rf
beta_range = np.linspace(0, df_capm['Beta'].max() * 1.1, 100)
sml_returns = rf + beta_range * market_excess_return

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=beta_range, y=sml_returns,
    mode='lines', name='Security Market Line',
    line=dict(color='royalblue', width=2, dash='dash')
))

colors = ['green' if a > 0 else 'red' for a in df_capm['Ann. Alpha']]
fig.add_trace(go.Scatter(
    x=df_capm['Beta'],
    y=df_capm['Ann. Return'],
    mode='markers+text',
    text=df_capm.index,
    textposition='top center',
    marker=dict(color=colors, size=10, line=dict(width=1, color='black')),
    name='Stocks (green = α > 0)',
    hovertemplate='<b>%{text}</b><br>Beta: %{x:.2f}<br>Return: %{y:.2%}<extra></extra>'
))

fig.update_layout(
    title='Security Market Line — Stocks vs CAPM Expectation',
    xaxis_title='Beta (Systematic Risk)',
    yaxis_title='Annualised Return',
    yaxis_tickformat='.0%',
    height=550,
    legend=dict(x=0.01, y=0.99)
)
st.plotly_chart(fig, use_container_width=True)
st.caption("🟢 Green = positive alpha (beats CAPM) | 🔴 Red = negative alpha (lags CAPM)")

# --- Rolling Beta ---
st.subheader("3. Rolling Beta")
st.markdown("Shows how each stock's market sensitivity **evolves over time** — static CAPM hides this.")

col1, col2 = st.columns([1, 2])
with col1:
    window = st.slider("Rolling Window (trading days)", 21, 126, 63,
                       help="63 ≈ 3 months  |  126 ≈ 6 months")
with col2:
    selected_rb = st.multiselect("Tickers to plot", tickers, default=tickers[:6],
                                  key='rolling_beta_tickers')

if selected_rb:
    # Compute rolling beta via rolling covariance / rolling variance
    mkt_var = market_returns.rolling(window).var()

    rolling_betas = pd.DataFrame(index=stock_returns.index)
    for t in selected_rb:
        rolling_cov = stock_returns[t].rolling(window).cov(market_returns)
        rolling_betas[t] = rolling_cov / mkt_var

    rolling_betas = rolling_betas.dropna()

    fig_rb = go.Figure()
    for t in selected_rb:
        fig_rb.add_trace(go.Scatter(
            x=rolling_betas.index, y=rolling_betas[t],
            mode='lines', name=t,
            hovertemplate=f'<b>{t}</b><br>Date: %{{x|%b %d %Y}}<br>β: %{{y:.2f}}<extra></extra>'
        ))

    fig_rb.add_hline(y=1.0, line_dash='dash', line_color='black', line_width=1,
                     annotation_text='β = 1 (market)', annotation_position='bottom right')
    fig_rb.add_hline(y=0.0, line_dash='dot', line_color='grey', line_width=1)

    fig_rb.update_layout(
        title=f'Rolling {window}-Day Beta vs {benchmark}',
        xaxis_title='Date',
        yaxis_title='Beta',
        height=480,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0)
    )
    st.plotly_chart(fig_rb, use_container_width=True)

    # Current vs static beta comparison table
    st.markdown("**Current Rolling Beta vs Static (Full-Period) Beta**")
    compare_rows = []
    for t in selected_rb:
        current_rb = rolling_betas[t].iloc[-1]
        static_b = df_capm.loc[t, 'Beta']
        delta = current_rb - static_b
        compare_rows.append({
            'Ticker': t,
            'Static Beta': static_b,
            f'Rolling Beta (last {window}d)': current_rb,
            'Δ (Rolling − Static)': delta,
            'Trend': '📈 Rising' if delta > 0.1 else ('📉 Falling' if delta < -0.1 else '➡️ Stable'),
        })
    df_rb_compare = pd.DataFrame(compare_rows).set_index('Ticker')
    st.dataframe(
        df_rb_compare.style.format({
            'Static Beta': '{:.3f}',
            f'Rolling Beta (last {window}d)': '{:.3f}',
            'Δ (Rolling − Static)': '{:+.3f}',
        }).background_gradient(subset=['Δ (Rolling − Static)'], cmap='RdYlGn'),
        use_container_width=True
    )
    st.caption("A rising rolling beta means the stock is becoming *more* correlated with the market — useful for hedging decisions.")

# --- Drawdown Analysis ---
st.subheader("4. Drawdown Analysis")

cum_returns = (1 + stock_returns).cumprod()
rolling_max = cum_returns.cummax()
drawdowns = (cum_returns / rolling_max) - 1

selected_dd = st.multiselect("Select tickers for drawdown chart",
                              tickers, default=tickers[:5])

if selected_dd:
    fig2 = px.area(drawdowns[selected_dd], title="Portfolio Drawdown Over Time",
                   labels={'value': 'Drawdown', 'index': 'Date'},
                   color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_layout(yaxis_tickformat='.0%', height=400)
    st.plotly_chart(fig2, use_container_width=True)

# Max drawdown table
max_dd = drawdowns.min().rename("Max Drawdown").to_frame()
max_dd['Recovery Date'] = drawdowns.apply(
    lambda col: col[col == col.min()].index[0].date()
)
st.dataframe(
    max_dd.style.format({'Max Drawdown': '{:.2%}'}),
    use_container_width=True
)

# --- Risk-Adjusted Metrics ---
st.subheader("5. Risk-Adjusted Return Metrics")

metrics = []
for t in tickers:
    r = stock_returns[t]
    ann_r = r.mean() * 252
    ann_v = r.std() * np.sqrt(252)
    sharpe = (ann_r - rf) / ann_v if ann_v > 0 else np.nan
    downside = r[r < 0].std() * np.sqrt(252)
    sortino = (ann_r - rf) / downside if downside > 0 else np.nan
    mdd = drawdowns[t].min()
    calmar = ann_r / abs(mdd) if mdd != 0 else np.nan
    metrics.append({
        'Ticker': t,
        'Ann. Return': ann_r,
        'Ann. Vol': ann_v,
        'Sharpe': sharpe,
        'Sortino': sortino,
        'Max DD': mdd,
        'Calmar': calmar,
    })

df_metrics = pd.DataFrame(metrics).set_index('Ticker').sort_values('Sharpe', ascending=False)

st.dataframe(
    df_metrics.style.format({
        'Ann. Return': '{:.2%}',
        'Ann. Vol': '{:.2%}',
        'Sharpe': '{:.2f}',
        'Sortino': '{:.2f}',
        'Max DD': '{:.2%}',
        'Calmar': '{:.2f}',
    }).background_gradient(subset=['Sharpe'], cmap='RdYlGn'),
    use_container_width=True,
    height=500
)
