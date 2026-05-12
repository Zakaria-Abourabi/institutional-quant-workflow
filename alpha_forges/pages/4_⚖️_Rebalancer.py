import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from theme import apply_theme, plotly_layout, EMERALD, GOLD, TEXT_MUTED, BG_SURFACE, BG_RAISED

st.header("⚖️ Live Portfolio Rebalancer")
apply_theme()

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

tickers = st.session_state['tickers']
raw_data = st.session_state['raw_data']

# FIX: raw_data is a DataFrame; get last row as a Series, then select only our tickers
last_prices_row = raw_data.iloc[-1]
prices = last_prices_row.reindex(tickers)

# Drop any tickers with missing prices
available = prices.dropna().index.tolist()
if len(available) < len(tickers):
    missing = set(tickers) - set(available)
    st.warning(f"No price data for: {', '.join(missing)}. These will be excluded.")
    tickers = available
    prices = prices[tickers]

st.subheader("1. Current Holdings")

input_data = pd.DataFrame({
    "Ticker": tickers,
    "Current Price ($)": prices[tickers].values.round(2),
    "Shares Owned": [0] * len(tickers),
    "Target Weight %": [round(100.0 / len(tickers), 2)] * len(tickers),
})

edited_df = st.data_editor(
    input_data,
    num_rows="fixed",
    disabled=["Ticker", "Current Price ($)"],
    use_container_width=True
)

# Validate target weights
total_target = edited_df["Target Weight %"].sum()
if abs(total_target - 100) > 0.5:
    st.warning(f"⚠️ Target weights sum to **{total_target:.1f}%** — they should sum to 100%. "
               f"Results will be normalised automatically.")

st.subheader("2. Cash Injection")
new_cash = st.number_input("Fresh Capital to Invest ($)", min_value=0.0, value=1000.0, step=100.0)

col1, col2 = st.columns([1, 3])
with col1:
    run = st.button("📊 Calculate Trade List", type="primary")

if run:
    df = edited_df.set_index("Ticker").copy()
    price_s = prices[tickers]

    current_values = price_s * df["Shares Owned"]
    total_current_val = float(current_values.sum())
    new_total_val = total_current_val + new_cash

    # Normalise weights so they always sum to 100 %
    raw_targets = df["Target Weight %"] / 100.0
    normalised_targets = raw_targets / raw_targets.sum()

    rebalance_report = []
    for t in tickers:
        target_val = new_total_val * normalised_targets[t]
        current_val = float(current_values[t])
        diff = target_val - current_val
        px_price = float(price_s[t])
        shares_delta = diff / px_price if px_price > 0 else 0

        rebalance_report.append({
            "Ticker": t,
            "Price ($)": round(px_price, 2),
            "Current Value ($)": round(current_val, 2),
            "Target Value ($)": round(target_val, 2),
            "Trade Amount ($)": round(abs(diff), 2),
            "Shares to Trade": round(abs(shares_delta), 4),
            "Action": "🟢 BUY" if diff > 1 else ("🔴 SELL" if diff < -1 else "⚪ HOLD"),
        })

    df_report = pd.DataFrame(rebalance_report)

    st.subheader("3. Trade List")
    st.dataframe(df_report, use_container_width=True)

    # Summary metrics
    buys = df_report[df_report["Action"].str.contains("BUY")]
    sells = df_report[df_report["Action"].str.contains("SELL")]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portfolio Value", f"${new_total_val:,.0f}")
    col2.metric("New Cash Added", f"${new_cash:,.0f}")
    col3.metric("Buy Orders", f"{len(buys)} (${buys['Trade Amount ($)'].sum():,.0f})")
    col4.metric("Sell Orders", f"{len(sells)} (${sells['Trade Amount ($)'].sum():,.0f})")

    # Waterfall chart — before vs after
    st.subheader("4. Rebalance Visualisation")
    fig = px.bar(
        df_report, x="Ticker",
        y=["Current Value ($)", "Target Value ($)"],
        barmode="group",
        title="Current vs. Target Portfolio Value by Ticker",
        labels={"value": "Value ($)", "variable": ""}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Action breakdown pie
    action_counts = df_report["Action"].value_counts()
    fig2 = px.pie(values=action_counts.values, names=action_counts.index,
                  title="Trade Action Breakdown",
                  color_discrete_map={
                      "🟢 BUY": "green", "🔴 SELL": "red", "⚪ HOLD": "grey"
                  })
    col_left, col_right = st.columns(2)
    col_left.plotly_chart(fig2, use_container_width=True)

    # Target weights pie
    fig3 = px.pie(
        values=normalised_targets.values,
        names=normalised_targets.index,
        title="Target Allocation"
    )
    col_right.plotly_chart(fig3, use_container_width=True)