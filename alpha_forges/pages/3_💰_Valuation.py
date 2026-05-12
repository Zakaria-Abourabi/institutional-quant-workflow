import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from theme import apply_theme, plotly_layout, EMERALD, GOLD, TEXT_MUTED, BG_SURFACE, BG_RAISED

st.header("💰 Fundamental Valuation")
apply_theme()

if 'returns' not in st.session_state:
    st.warning("Please sync data on the Home page first.")
    st.stop()

tickers = st.session_state['tickers']
rf = st.session_state['rf']


# --- Helper functions (from notebook Section 13) ---

def get_financial_item(df, possible_keys):
    df.index = df.index.astype(str).str.strip()
    for key in possible_keys:
        if key in df.index:
            val = df.loc[key].iloc[0]
            if pd.notnull(val):
                return float(val)
    return None


def calculate_wacc(stock_info, rf_rate):
    mkt_cap = stock_info.get('marketCap', 0) or 0
    total_debt = stock_info.get('totalDebt', 0) or 0
    total_val = mkt_cap + total_debt

    if total_val == 0:
        return rf_rate

    beta = stock_info.get('beta', 1.0) or 1.0
    erp = 0.0511  # equity risk premium 2026 estimate
    cost_of_equity = rf_rate + beta * erp

    interest_exp = abs(stock_info.get('interestExpense', 0) or 0)
    cost_of_debt = (interest_exp / total_debt) if total_debt > 0 else (rf_rate + 0.02)

    w_e = mkt_cap / total_val
    w_d = total_debt / total_val
    wacc = (w_e * cost_of_equity) + (w_d * cost_of_debt * 0.79)  # 21% tax
    return max(wacc, rf_rate)  # floor at rf


def run_dcf(info, wacc, growth_rate=0.08):
    fcf = info.get('freeCashflow', 0) or 0
    shares = info.get('sharesOutstanding', 1) or 1
    tg = 0.025  # terminal growth

    if fcf <= 0 or wacc <= tg:
        return None

    pv_fcfs = sum(
        (fcf * (1 + growth_rate) ** i) / (1 + wacc) ** i
        for i in range(1, 11)
    )
    fcf_y11 = fcf * (1 + growth_rate) ** 10 * (1 + tg)
    terminal_value = fcf_y11 / (wacc - tg)
    pv_terminal = terminal_value / (1 + wacc) ** 10

    fair_value = (pv_fcfs + pv_terminal) / shares
    return fair_value


def run_ddm(info, wacc):
    div = info.get('dividendRate', 0) or 0
    g = 0.025
    ke = wacc
    if (ke - g) <= 0 or div <= 0:
        return None
    return div / (ke - g)


def quality_gate(stock, info):
    try:
        bs = stock.balance_sheet
        inc = stock.financials
        if bs.empty or inc.empty:
            return None, None, None

        ebit = get_financial_item(inc, ['EBIT', 'Operating Income', 'OperatingIncome'])
        interest = get_financial_item(inc, ['Interest Expense', 'InterestExpense',
                                            'Interest Expense Non Operating'])
        assets = get_financial_item(bs, ['Total Assets', 'TotalAssets'])
        curr_liab = get_financial_item(bs, ['Total Current Liabilities', 'Current Liabilities',
                                            'TotalCurrentLiabilities']) or 0

        if ebit is None or assets is None:
            return None, None, None

        interest_coverage = float('inf') if (interest is None or interest >= 0) \
            else ebit / abs(interest)
        invested_capital = assets - curr_liab
        roic = (ebit * 0.79) / invested_capital if invested_capital > 0 else None

        passed = (roic is not None and roic > 0.15 and
                  (interest_coverage > 5 or interest_coverage == float('inf')))
        return roic, interest_coverage, passed
    except Exception:
        return None, None, None


# --- UI ---
st.subheader("Valuation Settings")
col1, col2 = st.columns(2)
with col1:
    growth_rate = st.slider("DCF Growth Rate (Stage 1, 10yr)", 0.02, 0.20, 0.08, step=0.01,
                             format="%.0f%%")
with col2:
    selected_tickers = st.multiselect("Tickers to Value", tickers, default=tickers[:10])

if not selected_tickers:
    st.info("Select at least one ticker above.")
    st.stop()

if st.button("🔍 Run Valuation (fetches live fundamentals)"):
    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(selected_tickers):
        status.text(f"Valuing {ticker}... ({i+1}/{len(selected_tickers)})")
        try:
            stk = yf.Ticker(ticker)
            info = stk.info
            sector = info.get('sector', 'Unknown')
            price = info.get('currentPrice', None) or info.get('previousClose', None)

            wacc = calculate_wacc(info, rf)
            fair_value = run_dcf(info, wacc, growth_rate)

            # Fallback to DDM if no positive FCF
            method = 'DCF'
            if fair_value is None:
                fair_value = run_ddm(info, wacc)
                method = 'DDM'

            roic, coverage, passed = quality_gate(stk, info)

            mos = None
            verdict = '—'
            if fair_value and price and price > 0 and fair_value > 0:
                mos = (fair_value - price) / fair_value
                verdict = '✅ BUY/HOLD' if mos > 0.15 else ('⚠️ OVERVALUED' if mos < -0.10 else '🟡 FAIR VALUE')

            results.append({
                'Ticker': ticker,
                'Sector': sector,
                'Method': method,
                'WACC': wacc,
                'Market Price': price,
                'Intrinsic Value': fair_value,
                'Margin of Safety': mos,
                'ROIC': roic,
                'Quality': '✅' if passed else ('❌' if passed is not None else '—'),
                'Verdict': verdict,
            })
        except Exception as e:
            results.append({
                'Ticker': ticker, 'Sector': '—', 'Method': 'Error',
                'WACC': None, 'Market Price': None, 'Intrinsic Value': None,
                'Margin of Safety': None, 'ROIC': None,
                'Quality': '—', 'Verdict': f'⚠️ {str(e)[:40]}'
            })

        progress.progress((i + 1) / len(selected_tickers))

    status.empty()
    progress.empty()

    df_val = pd.DataFrame(results).set_index('Ticker')
    st.session_state['valuation_df'] = df_val

if 'valuation_df' in st.session_state:
    df_val = st.session_state['valuation_df']

    st.subheader("📋 Valuation Results")
    fmt_cols = {
        'WACC': '{:.2%}',
        'Market Price': '${:.2f}',
        'Intrinsic Value': '${:.2f}',
        'Margin of Safety': '{:.1%}',
        'ROIC': '{:.2%}',
    }
    # Only format columns that exist and have numeric data
    safe_fmt = {k: v for k, v in fmt_cols.items()
                if k in df_val.columns and pd.api.types.is_numeric_dtype(df_val[k])}

    st.dataframe(
        df_val.style.format(safe_fmt, na_rep='N/A')
        .applymap(lambda v: 'color: green' if isinstance(v, str) and '✅' in v else
                            ('color: red' if isinstance(v, str) and '⚠️' in v else ''),
                  subset=['Verdict']),
        use_container_width=True
    )

    # MoS chart
    plot_df = df_val.dropna(subset=['Margin of Safety'])
    if not plot_df.empty:
        st.subheader("📊 Margin of Safety by Ticker")
        fig = px.bar(
            plot_df.reset_index(), x='Ticker', y='Margin of Safety',
            color='Margin of Safety',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            title="Margin of Safety (positive = undervalued)",
            labels={'Margin of Safety': 'MoS'}
        )
        fig.update_layout(yaxis_tickformat='.0%', height=400)
        fig.add_hline(y=0.15, line_dash='dash', line_color='green',
                      annotation_text="15% MoS threshold")
        st.plotly_chart(fig, use_container_width=True)

    # Price vs Fair Value
    plot_df2 = df_val.dropna(subset=['Market Price', 'Intrinsic Value'])
    if not plot_df2.empty:
        st.subheader("📈 Market Price vs Intrinsic Value")
        import plotly.graph_objects as go
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Market Price', x=plot_df2.index,
                               y=plot_df2['Market Price'], marker_color='steelblue'))
        fig2.add_trace(go.Bar(name='Intrinsic Value', x=plot_df2.index,
                               y=plot_df2['Intrinsic Value'], marker_color='darkorange'))
        fig2.update_layout(barmode='group', title='Market Price vs Intrinsic Value',
                           yaxis_title='USD ($)', height=450)
        st.plotly_chart(fig2, use_container_width=True)

    st.caption("⚠️ DCF valuations are highly sensitive to growth rate and WACC assumptions. "
               "Not financial advice.")