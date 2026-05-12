import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import plotly.express as px
import plotly.graph_objects as go

st.header("🔬 Advanced Factor Models")

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

returns = st.session_state['returns']
tickers = st.session_state['tickers']
rf = st.session_state['rf']
benchmark = st.session_state['benchmark']

stock_returns = returns[tickers]
market_returns = returns[benchmark]

tab1, tab2, tab3 = st.tabs(["📊 Walk-Forward Test", "🌑 Black-Litterman", "🔄 Regime Detection"])

# ─────────────────────────────────────────────
# TAB 1: Walk-Forward Testing (Section 14)
# ─────────────────────────────────────────────
with tab1:
    st.subheader("Walk-Forward Out-of-Sample Testing")
    st.markdown("Trains on a rolling window, then evaluates on the next out-of-sample period.")

    col1, col2 = st.columns(2)
    with col1:
        train_months = st.slider("Training Window (months)", 3, 12, 6)
        oos_months = st.slider("OOS Window (months)", 1, 6, 3)
    with col2:
        max_w_wf = st.slider("Max Weight per Asset", 0.10, 0.50, 0.30)

    def optimize_weights(ret_df, rf_rate, max_weight=0.30):
        tks = ret_df.columns.tolist()
        n = len(tks)
        ann_ret = ret_df.mean() * 252
        cov = ret_df.cov() * 252

        def neg_sharpe(w):
            r = np.dot(w, ann_ret)
            v = np.sqrt(np.dot(w.T, np.dot(cov.values, w)))
            return -((r - rf_rate) / v) if v > 0 else 0

        res = minimize(neg_sharpe, np.full(n, 1/n), method='SLSQP',
                       bounds=[(0, max_weight)] * n,
                       constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        if res.success:
            return pd.Series(res.x, index=tks)
        return pd.Series(np.full(n, 1/n), index=tks)

    if st.button("▶️ Run Walk-Forward Test"):
        with st.spinner("Running walk-forward optimization..."):
            all_dates = stock_returns.index
            train_days = train_months * 21
            oos_days = oos_months * 21

            wf_results = []
            i = train_days
            period_num = 1

            while i + oos_days <= len(all_dates):
                train_slice = stock_returns.iloc[i - train_days:i]
                oos_slice = stock_returns.iloc[i:i + oos_days]

                w = optimize_weights(train_slice, rf, max_w_wf)
                oos_port = oos_slice.dot(w)

                ann_r = oos_port.mean() * 252
                ann_v = oos_port.std() * np.sqrt(252)
                sharpe = (ann_r - rf) / ann_v if ann_v > 0 else np.nan

                period_label = f"P{period_num} ({all_dates[i].strftime('%b %y')})"
                wf_results.append({
                    'Period': period_label,
                    'OOS Ann. Return': ann_r,
                    'OOS Volatility': ann_v,
                    'OOS Sharpe': sharpe,
                })
                i += oos_days
                period_num += 1

            wf_df = pd.DataFrame(wf_results).set_index('Period')
            st.session_state['wf_df'] = wf_df

    if 'wf_df' in st.session_state:
        wf_df = st.session_state['wf_df']

        col1, col2, col3 = st.columns(3)
        col1.metric("Mean OOS Sharpe", f"{wf_df['OOS Sharpe'].mean():.2f}")
        col2.metric("Mean OOS Return", f"{wf_df['OOS Ann. Return'].mean():.2%}")
        col3.metric("Periods Tested", len(wf_df))

        fig1 = px.bar(wf_df.reset_index(), x='Period', y='OOS Sharpe',
                      color='OOS Sharpe', color_continuous_scale='RdYlGn',
                      color_continuous_midpoint=0,
                      title='Walk-Forward OOS Sharpe Ratio by Period')
        fig1.add_hline(y=wf_df['OOS Sharpe'].mean(), line_dash='dash',
                       line_color='blue', annotation_text="Mean")
        fig1.update_layout(height=350)
        st.plotly_chart(fig1, use_container_width=True)

        cum_oos = (1 + wf_df['OOS Ann. Return'] / 12).cumprod() - 1
        fig2 = go.Figure(go.Scatter(x=list(cum_oos.index), y=cum_oos.values,
                                    mode='lines+markers', line=dict(color='steelblue', width=2)))
        fig2.add_hline(y=0, line_dash='dash', line_color='black')
        fig2.update_layout(title='Cumulative Out-of-Sample Return',
                           yaxis_tickformat='.0%', height=350)
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(wf_df.style.format({
            'OOS Ann. Return': '{:.2%}', 'OOS Volatility': '{:.2%}', 'OOS Sharpe': '{:.2f}'
        }), use_container_width=True)


# ─────────────────────────────────────────────
# TAB 2: Black-Litterman (Section 17)
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Black-Litterman Portfolio Optimization")
    st.markdown("""
    Black-Litterman blends **market equilibrium** (implied returns from market caps)
    with your **subjective views** to produce a combined expected return vector.
    """)

    n = len(tickers)
    cov_ann = stock_returns.cov() * 252
    ann_ret = stock_returns.mean() * 252

    # Market equilibrium: equal-weight proxy
    delta = 2.5  # risk aversion
    w_eq = np.full(n, 1.0 / n)
    pi = delta * cov_ann.values @ w_eq  # implied equilibrium returns

    st.subheader("1. Enter Your Views")
    st.markdown("For each view, pick a ticker you expect to **outperform** and by how much.")

    n_views = st.slider("Number of Views", 1, min(5, n), 2)
    views_P, views_Q = [], []
    tau = st.slider("Confidence (τ, lower = more weight on equilibrium)", 0.01, 0.50, 0.05)

    for i in range(n_views):
        cols = st.columns([2, 2, 2])
        with cols[0]:
            long_t = st.selectbox(f"View {i+1}: LONG ticker", tickers,
                                  key=f"long_{i}", index=min(i, n-1))
        with cols[1]:
            short_t = st.selectbox(f"View {i+1}: SHORT ticker (or None)",
                                   ['— (Absolute View)'] + tickers,
                                   key=f"short_{i}", index=0)
        with cols[2]:
            view_ret = st.number_input(f"Expected excess return (%)",
                                        value=10.0, step=1.0, key=f"ret_{i}") / 100

        p_row = np.zeros(n)
        p_row[tickers.index(long_t)] = 1.0
        if short_t != '— (Absolute View)' and short_t != long_t:
            p_row[tickers.index(short_t)] = -1.0
        views_P.append(p_row)
        views_Q.append(view_ret)

    if st.button("⚙️ Run Black-Litterman"):
        P = np.array(views_P)
        Q = np.array(views_Q)
        k = len(Q)

        omega = np.diag(np.diag(tau * P @ cov_ann.values @ P.T))

        # BL posterior expected return
        cov_pi = tau * cov_ann.values
        A = np.linalg.inv(np.linalg.inv(cov_pi) + P.T @ np.linalg.inv(omega) @ P)
        bl_mu = A @ (np.linalg.inv(cov_pi) @ pi + P.T @ np.linalg.inv(omega) @ Q)

        # BL posterior covariance
        bl_cov = cov_ann.values + A

        # Optimise on BL returns
        def neg_sharpe_bl(w):
            r = np.dot(w, bl_mu)
            v = np.sqrt(np.dot(w.T, np.dot(bl_cov, w)))
            return -((r - rf) / v) if v > 0 else 0

        res_bl = minimize(neg_sharpe_bl, w_eq, method='SLSQP',
                          bounds=[(0, 0.30)] * n,
                          constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        if res_bl.success:
            bl_weights = pd.Series(res_bl.x, index=tickers)
            eq_weights = pd.Series(w_eq, index=tickers)

            comparison = pd.DataFrame({
                'Equilibrium': eq_weights,
                'BL Optimal': bl_weights,
                'Implied Return (eq.)': pd.Series(pi, index=tickers),
                'BL Return': pd.Series(bl_mu, index=tickers),
            })

            st.subheader("Results")
            col1, col2 = st.columns(2)
            bl_r = np.dot(res_bl.x, bl_mu)
            bl_v = np.sqrt(np.dot(res_bl.x, np.dot(bl_cov, res_bl.x)))
            col1.metric("BL Portfolio Return", f"{bl_r:.2%}")
            col2.metric("BL Portfolio Sharpe", f"{(bl_r - rf)/bl_v:.2f}")

            fig = px.bar(comparison.reset_index(), x='index',
                         y=['Equilibrium', 'BL Optimal'],
                         barmode='group',
                         title='Equilibrium vs. Black-Litterman Weights',
                         labels={'index': 'Ticker', 'value': 'Weight'})
            fig.update_layout(yaxis_tickformat='.0%', height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(comparison.style.format({
                'Equilibrium': '{:.2%}',
                'BL Optimal': '{:.2%}',
                'Implied Return (eq.)': '{:.2%}',
                'BL Return': '{:.2%}',
            }), use_container_width=True)
        else:
            st.error("BL optimizer did not converge.")


# ─────────────────────────────────────────────
# TAB 3: Regime Detection (Section 18)
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Market Regime Detection (HMM-Style via Volatility Clustering)")
    st.markdown("""
    Detects **Calm** vs **Stress** regimes using rolling volatility thresholding
    (a transparent proxy for Hidden Markov Models used in the notebook).
    """)

    bench_ret = market_returns.copy()
    roll_vol = bench_ret.rolling(21).std() * np.sqrt(252)  # 1-month rolling annualised vol

    vol_threshold = st.slider(
        "Volatility Threshold (stress vs calm)",
        float(roll_vol.quantile(0.25)),
        float(roll_vol.quantile(0.90)),
        float(roll_vol.median()),
        step=0.01,
        format="%.2f"
    )

    regime_series = pd.Series(
        np.where(roll_vol >= vol_threshold, 'Stress', 'Calm'),
        index=roll_vol.index,
        name='Regime'
    ).dropna()

    # Remove NaN rows from rolling
    regime_series = regime_series[roll_vol.notna()]

    # SPY price chart with regimes
    spy_price = st.session_state['raw_data'][benchmark].dropna()
    regime_aligned = regime_series.reindex(spy_price.index)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spy_price.index, y=spy_price.values,
                             mode='lines', name=f'{benchmark} Price',
                             line=dict(color='black', width=1.5)))

    # Add shaded regime regions
    prev_regime = None
    span_start = None
    for date, regime in regime_aligned.items():
        if regime != prev_regime:
            if prev_regime == 'Stress' and span_start is not None:
                fig.add_vrect(x0=span_start, x1=date, fillcolor='red',
                              opacity=0.15, layer='below', line_width=0)
            elif prev_regime == 'Calm' and span_start is not None:
                fig.add_vrect(x0=span_start, x1=date, fillcolor='green',
                              opacity=0.10, layer='below', line_width=0)
            span_start = date
            prev_regime = regime

    fig.update_layout(
        title=f'{benchmark} Price with Detected Market Regimes',
        yaxis_title='Price', height=450,
    )
    # Legend annotation
    fig.add_annotation(x=0.01, y=0.95, xref='paper', yref='paper',
                       text='🟢 Calm | 🔴 Stress', showarrow=False,
                       bgcolor='white', bordercolor='grey')
    st.plotly_chart(fig, use_container_width=True)

    # Regime stats
    st.subheader("Regime-Conditional Portfolio Statistics")
    weights_eq = np.full(len(tickers), 1.0 / len(tickers))
    port_daily = stock_returns.dot(weights_eq)
    port_aligned = port_daily.reindex(regime_series.index).dropna()
    regime_port = regime_series.reindex(port_aligned.index)

    regime_stats = []
    for label in ['Calm', 'Stress']:
        mask = regime_port == label
        r = port_aligned[mask]
        if len(r) < 5:
            continue
        ann_r = r.mean() * 252
        ann_v = r.std() * np.sqrt(252)
        sharpe = (ann_r - rf) / ann_v if ann_v > 0 else np.nan
        mdd = ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min()
        days = mask.sum()
        regime_stats.append({
            'Regime': label,
            'Days': days,
            'Ann. Return': ann_r,
            'Volatility': ann_v,
            'Sharpe': sharpe,
            'Max DD': mdd,
        })

    df_reg = pd.DataFrame(regime_stats).set_index('Regime')
    st.dataframe(df_reg.style.format({
        'Ann. Return': '{:.2%}', 'Volatility': '{:.2%}',
        'Sharpe': '{:.2f}', 'Max DD': '{:.2%}'
    }), use_container_width=True)

    current_regime = regime_series.iloc[-1]
    regime_color = "🟢" if current_regime == "Calm" else "🔴"
    st.metric("Current Detected Regime", f"{regime_color} {current_regime}")

    # Regime-aware optimization
    st.subheader("Regime-Aware Portfolio Optimization")
    if st.button("⚙️ Optimize for Current Regime"):
        regime_mask = regime_series == current_regime
        regime_ret = stock_returns.reindex(regime_series[regime_mask].index).dropna()

        if len(regime_ret) < 30:
            st.warning("Not enough data in this regime to optimize reliably.")
        else:
            n = len(tickers)
            ann_ret_reg = regime_ret.mean() * 252
            cov_reg = regime_ret.cov() * 252

            def neg_sh(w):
                r = np.dot(w, ann_ret_reg)
                v = np.sqrt(np.dot(w.T, np.dot(cov_reg.values, w)))
                return -((r - rf) / v) if v > 0 else 0

            res_ra = minimize(neg_sh, np.full(n, 1/n), method='SLSQP',
                              bounds=[(0, 0.30)] * n,
                              constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

            if res_ra.success:
                ra_w = pd.Series(res_ra.x, index=tickers)
                display_ra = ra_w[ra_w > 0.005].sort_values(ascending=False)

                col1, col2 = st.columns(2)
                with col1:
                    fig_ra = px.pie(values=display_ra.values, names=display_ra.index,
                                    title=f"Regime-Optimal Weights ({current_regime})")
                    st.plotly_chart(fig_ra, use_container_width=True)
                with col2:
                    st.dataframe(
                        display_ra.rename("Weight").to_frame()
                        .style.format({'Weight': '{:.2%}'}),
                        use_container_width=True
                    )
            else:
                st.error("Regime optimizer did not converge.")
