import streamlit as st
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize
import plotly.express as px
import plotly.graph_objects as go
from theme import apply_theme, plotly_layout, EMERALD, GOLD, TEXT_MUTED, BG_SURFACE, BG_RAISED

st.header("🎯 Advanced Optimization Engine")
apply_theme()

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

returns = st.session_state['returns']
tickers = st.session_state['tickers']
rf = st.session_state['rf']

stock_returns = returns[tickers]

# --- Settings ---
st.subheader("Optimization Settings")
col1, col2 = st.columns(2)
with col1:
    max_w = st.slider("Max Single Asset Weight", 0.05, 1.0, 0.20, step=0.05)
    use_shrinkage = st.checkbox("Use Ledoit-Wolf Covariance Shrinkage", value=True)
with col2:
    n_sim = st.slider("Monte Carlo Simulations (Efficient Frontier)", 10000, 100000, 50000, step=10000)

mean_ret = stock_returns.mean() * 252
cov_ann = stock_returns.cov() * 252

if use_shrinkage:
    lw = LedoitWolf().fit(stock_returns.values)
    cov_matrix = pd.DataFrame(lw.covariance_ * 252, index=tickers, columns=tickers)
    shrink_coef = lw.shrinkage_
    st.info(f"🔬 Ledoit-Wolf shrinkage applied | coefficient = **{shrink_coef:.4f}** "
            f"| Condition number improved "
            f"**{np.linalg.cond(cov_ann.values) / np.linalg.cond(cov_matrix.values):.1f}x**")
else:
    cov_matrix = cov_ann

# --- Constrained Max-Sharpe Optimization ---
st.subheader("1. Constrained Max-Sharpe Portfolio")

n = len(tickers)

def negative_sharpe(weights):
    r = np.dot(weights, mean_ret)
    v = np.sqrt(np.dot(weights.T, np.dot(cov_matrix.values, weights)))
    if v == 0:
        return 0
    return -((r - rf) / v)

init_guess = np.full(n, 1.0 / n)
bounds = [(0.0, max_w) for _ in range(n)]
constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

res = minimize(negative_sharpe, init_guess, method='SLSQP',
               bounds=bounds, constraints=constraints)

if res.success:
    opt_weights = pd.Series(res.x, index=tickers)
    opt_sharpe = -res.fun
    opt_ret = np.dot(res.x, mean_ret)
    opt_vol = np.sqrt(np.dot(res.x.T, np.dot(cov_matrix.values, res.x)))

    col1, col2, col3 = st.columns(3)
    col1.metric("Expected Annual Return", f"{opt_ret:.2%}")
    col2.metric("Portfolio Volatility", f"{opt_vol:.2%}")
    col3.metric("Sharpe Ratio", f"{opt_sharpe:.2f}")

    # Filter tiny weights
    display_weights = opt_weights[opt_weights > 0.005].sort_values(ascending=False)

    col_pie, col_bar = st.columns(2)
    with col_pie:
        fig_pie = px.pie(values=display_weights.values, names=display_weights.index,
                         title="Optimal Allocation")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_bar:
        fig_bar = px.bar(x=display_weights.index, y=display_weights.values,
                         labels={'x': 'Ticker', 'y': 'Weight'},
                         title="Weight Distribution",
                         color=display_weights.values,
                         color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis_tickformat='.0%', showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.dataframe(
        display_weights.rename("Optimal Weight").to_frame()
        .style.format({'Optimal Weight': '{:.2%}'}),
        use_container_width=True
    )
else:
    st.error(f"Optimizer did not converge: {res.message}")

# --- Risk Parity ---
st.subheader("2. Risk Parity Portfolio")

def risk_parity_objective(weights):
    w = np.array(weights)
    port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix.values, w)))
    marginal_risk = np.dot(cov_matrix.values, w) / port_vol
    risk_contrib = w * marginal_risk
    target = port_vol / n
    return np.sum((risk_contrib - target) ** 2)

rp_res = minimize(risk_parity_objective, init_guess, method='SLSQP',
                  bounds=[(0.001, 1.0) for _ in range(n)],
                  constraints=constraints)

if rp_res.success:
    rp_weights = pd.Series(rp_res.x / rp_res.x.sum(), index=tickers)
    rp_ret = np.dot(rp_weights, mean_ret)
    rp_vol = np.sqrt(np.dot(rp_weights.T, np.dot(cov_matrix.values, rp_weights)))
    rp_sharpe = (rp_ret - rf) / rp_vol

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Parity Return", f"{rp_ret:.2%}")
    col2.metric("Risk Parity Volatility", f"{rp_vol:.2%}")
    col3.metric("Risk Parity Sharpe", f"{rp_sharpe:.2f}")

    display_rp = rp_weights[rp_weights > 0.005].sort_values(ascending=False)
    fig_rp = px.bar(x=display_rp.index, y=display_rp.values,
                    title="Risk Parity Weights",
                    labels={'x': 'Ticker', 'y': 'Weight'},
                    color=display_rp.values,
                    color_continuous_scale='Viridis')
    fig_rp.update_layout(yaxis_tickformat='.0%', showlegend=False)
    st.plotly_chart(fig_rp, use_container_width=True)

# --- Efficient Frontier ---
st.subheader("3. Efficient Frontier (Monte Carlo)")

if st.button("🚀 Run Monte Carlo Simulation"):
    with st.spinner(f"Simulating {n_sim:,} portfolios..."):
        sim_returns, sim_vols, sim_sharpes, sim_weights = [], [], [], []

        for _ in range(n_sim):
            w = np.random.random(n)
            w /= w.sum()
            r = np.dot(w, mean_ret)
            v = np.sqrt(np.dot(w.T, np.dot(cov_matrix.values, w)))
            sim_returns.append(r)
            sim_vols.append(v)
            sim_sharpes.append((r - rf) / v)
            sim_weights.append(w)

        sim_returns = np.array(sim_returns)
        sim_vols = np.array(sim_vols)
        sim_sharpes = np.array(sim_sharpes)

        best_idx = sim_sharpes.argmax()

        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(
            x=sim_vols, y=sim_returns,
            mode='markers',
            marker=dict(color=sim_sharpes, colorscale='Viridis', size=3,
                        opacity=0.4, colorbar=dict(title='Sharpe')),
            name='Simulated Portfolios'
        ))
        fig_ef.add_trace(go.Scatter(
            x=[sim_vols[best_idx]], y=[sim_returns[best_idx]],
            mode='markers', marker=dict(color='red', size=18, symbol='star'),
            name=f'Max Sharpe ({sim_sharpes[best_idx]:.2f})'
        ))
        if res.success:
            fig_ef.add_trace(go.Scatter(
                x=[opt_vol], y=[opt_ret],
                mode='markers', marker=dict(color='orange', size=15, symbol='diamond'),
                name=f'Constrained Max Sharpe ({opt_sharpe:.2f})'
            ))
        fig_ef.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1A1F2E",
            title='Efficient Frontier — Monte Carlo Simulation',
            xaxis_title='Volatility (σ)',
            yaxis_title='Expected Return',
            xaxis_tickformat='.0%',
            yaxis_tickformat='.0%',
            height=550
        )
        st.plotly_chart(fig_ef, use_container_width=True)

        mc_best_weights = pd.Series(sim_weights[best_idx], index=tickers)
        mc_display = mc_best_weights[mc_best_weights > 0.01].sort_values(ascending=False)
        st.write("**Unconstrained MC Max-Sharpe weights:**")
        st.dataframe(
            mc_display.rename("Weight").to_frame().style.format({'Weight': '{:.2%}'}),
            use_container_width=True
        )