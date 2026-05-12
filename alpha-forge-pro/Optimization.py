import streamlit as st
import numpy as np
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize
import plotly.express as px

st.header("🎯 Advanced Optimization Engine")

if 'returns' not in st.session_state:
    st.stop()

returns = st.session_state['returns'][st.session_state['tickers']]
rf = st.session_state['rf']

st.write("Using **Ledoit-Wolf Covariance Shrinkage** to reduce statistical noise.")

# --- Ledoit-Wolf Implementation (Section 15) ---
lw = LedoitWolf().fit(returns.values)
shrunk_cov = lw.covariance_ * 252
mean_ret = returns.mean() * 252

# Optimization settings
max_w = st.slider("Max Single Asset Weight", 0.1, 1.0, 0.25)

def obj_func(w):
    port_ret = np.dot(w, mean_ret)
    port_vol = np.sqrt(np.dot(w.T, np.dot(shrunk_cov, w)))
    return -((port_ret - rf) / port_vol)

n = len(returns.columns)
res = minimize(obj_func, np.full(n, 1/n), 
               bounds=[(0, max_w) for _ in range(n)],
               constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

if res.success:
    weights = pd.Series(res.x, index=returns.columns)
    weights = weights[weights > 0.01].sort_values()
    
    fig = px.pie(values=weights.values, names=weights.index, title="Optimal Allocation")
    st.plotly_chart(fig)
    
    st.metric("Expected Annual Return", f"{np.dot(res.x, mean_ret):.2%}")
    st.metric("Portfolio Volatility (Shrunk)", f"{np.sqrt(np.dot(res.x.T, np.dot(shrunk_cov, res.x))):.2%}")