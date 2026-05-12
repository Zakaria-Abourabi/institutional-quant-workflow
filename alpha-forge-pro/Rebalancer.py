import streamlit as st
import pandas as pd

st.header("⚖️ Live Portfolio Rebalancer")

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

tickers = st.session_state['tickers']
prices = st.session_state['raw_data'].iloc[-1]

st.subheader("1. Enter Current Holdings")
# Create an editable table for the user
input_data = pd.DataFrame({
    "Ticker": tickers,
    "Shares Owned": [0] * len(tickers),
    "Target Weight %": [100/len(tickers)] * len(tickers)
})

edited_df = st.data_editor(input_data, num_rows="dynamic")

st.subheader("2. Cash Injection")
new_cash = st.number_input("Fresh Capital to Invest ($)", min_value=0, value=1000)

if st.button("Calculate Trade List"):
    # Math logic from Section 12 of your notebook
    current_values = prices[tickers] * edited_df.set_index("Ticker")["Shares Owned"]
    total_current_val = current_values.sum()
    new_total_val = total_current_val + new_cash
    
    targets = edited_df.set_index("Ticker")["Target Weight %"] / 100
    
    rebalance_report = []
    for t in tickers:
        target_val = new_total_val * targets[t]
        current_val = current_values[t]
        diff = target_val - current_val
        
        rebalance_report.append({
            "Ticker": t,
            "Current Value": f"${current_val:,.2f}",
            "Target Value": f"${target_val:,.2f}",
            "Action": "BUY" if diff > 0 else "HOLD/SELL",
            "Amount ($)": abs(diff)
        })
        
    st.table(pd.DataFrame(rebalance_report))