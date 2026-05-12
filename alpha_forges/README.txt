================================================================================
  ALPHA FORGE PRO — INSTITUTIONAL QUANTITATIVE PORTFOLIO ANALYSIS SUITE
  README & PROJECT DOCUMENTATION
================================================================================

  Author      : Zakaria
  Stack        : Python 3.10+ · Streamlit · yfinance · pandas · NumPy · SciPy
                 scikit-learn · statsmodels · Plotly
  Launch       : streamlit run app.py
  Last updated : May 2026

--------------------------------------------------------------------------------
TABLE OF CONTENTS
--------------------------------------------------------------------------------

  1.  Project Overview
  2.  Repository Structure
  3.  Installation & Quick Start
  4.  Architecture: How the App Works
  5.  Page-by-Page Feature Reference
        5.1  Home — Global Configuration & Universe Overview
        5.2  Risk & CAPM
        5.3  Advanced Optimization Engine
        5.4  Fundamental Valuation
        5.5  Portfolio Rebalancer
        5.6  Advanced Models (Walk-Forward · Black-Litterman · Regime Detection)
        5.7  Fama-French Three-Factor Model
  6.  Mathematical Reference
        6.1  CAPM & Alpha
        6.2  Rolling Beta
        6.3  Sharpe, Sortino & Calmar Ratios
        6.4  Ledoit-Wolf Covariance Shrinkage
        6.5  Max-Sharpe Optimisation (SLSQP)
        6.6  Risk Parity
        6.7  Monte Carlo Efficient Frontier
        6.8  DCF Valuation
        6.9  WACC
        6.10 Dividend Discount Model (DDM)
        6.11 Walk-Forward Testing
        6.12 Black-Litterman Model
        6.13 Regime Detection
        6.14 Fama-French Three-Factor Model
  7.  Data Sources & Refresh Policy
  8.  Known Limitations & Assumptions
  9.  Extending the App
  10. Disclaimer

================================================================================
1. PROJECT OVERVIEW
================================================================================

Alpha Forge Pro is a self-contained, browser-based quantitative finance toolkit
built on top of Streamlit. It was conceived as the interactive front-end to a
Jupyter notebook covering 18 sections of portfolio theory (data ingestion through
regime detection), with every analysis accessible through a point-and-click UI —
no code required at runtime.

The suite covers the full institutional workflow:

  · Data ingestion and universe management (yfinance, live prices)
  · Risk decomposition: CAPM, rolling beta, drawdown, VaR-style metrics
  · Portfolio construction: mean-variance, risk parity, Black-Litterman
  · Covariance estimation: sample vs. Ledoit-Wolf shrinkage
  · Out-of-sample validation: walk-forward testing
  · Fundamental valuation: DCF and DDM with live financials
  · Factor attribution: Fama-French 3-factor OLS regression
  · Regime-aware investing: volatility-clustering regime detection

All pages share a single data layer stored in Streamlit's session state, so
syncing the market data once on the Home page propagates instantly to every
other tab.

================================================================================
2. REPOSITORY STRUCTURE
================================================================================

  alpha_forge/
  │
  ├── app.py                          ← Entry point. Global sidebar + Home dashboard.
  ├── requirements.txt                ← All Python dependencies (pip install -r).
  ├── README.txt                      ← This file.
  │
  └── pages/                          ← Streamlit multi-page router (auto-discovered).
      ├── 1_📐_Risk_&_CAPM.py         ← CAPM regression, rolling beta, drawdown, metrics.
      ├── 2_🎯_Optimization.py        ← Max-Sharpe, Risk Parity, Efficient Frontier.
      ├── 3_💰_Valuation.py           ← DCF / DDM fundamental valuation.
      ├── 4_⚖️_Rebalancer.py          ← Live portfolio rebalancing trade list.
      ├── 5_🔬_Advanced_Models.py     ← Walk-Forward, Black-Litterman, Regime Detection.
      └── 6_📊_Fama_French.py         ← Fama-French 3-factor model & factor loadings.

Streamlit's multi-page convention: any .py file placed in the pages/ directory
is automatically added to the sidebar navigation in alphabetical/numeric order.
The numeric prefix (1_, 2_, …) controls the display order.

================================================================================
3. INSTALLATION & QUICK START
================================================================================

PREREQUISITES
  · Python 3.10 or higher
  · pip (comes with Python)
  · Internet connection (live market data is fetched from Yahoo Finance)

STEP 1 — Clone or download the repository
  -------------------------------------------------------
  git clone https://github.com/<your-username>/alpha-forge.git
  cd alpha-forge/alpha_forge
  -------------------------------------------------------
  Or simply unzip the downloaded archive and navigate into the alpha_forge/ folder.

STEP 2 — (Recommended) Create a virtual environment
  -------------------------------------------------------
  python3 -m venv venv
  source venv/bin/activate          # macOS / Linux
  venv\Scripts\activate             # Windows
  -------------------------------------------------------
  This keeps the project's dependencies isolated from your system Python.

STEP 3 — Install dependencies
  -------------------------------------------------------
  pip install -r requirements.txt
  -------------------------------------------------------
  This installs:
    streamlit        — web UI framework
    yfinance         — Yahoo Finance market data
    pandas           — data manipulation
    numpy            — numerical computing
    scipy            — optimisation (SLSQP solver)
    scikit-learn     — Ledoit-Wolf covariance estimator
    statsmodels      — OLS regression (CAPM, FF3)
    plotly           — interactive charts

STEP 4 — Launch the app
  -------------------------------------------------------
  streamlit run app.py
  -------------------------------------------------------
  Streamlit will print a local URL (default: http://localhost:8501).
  Open it in any browser. The app hot-reloads automatically if you edit source files.

STEP 5 — First use
  1. The sidebar shows a pre-loaded list of 31 tickers. Edit freely.
  2. Set your desired start date (more history = more stable covariance estimates;
     recommend at least 1 year).
  3. Click "Sync Market Data". Wait ~10-20 seconds for yfinance to download.
  4. Navigate to any page from the sidebar.

================================================================================
4. ARCHITECTURE: HOW THE APP WORKS
================================================================================

DATA FLOW
  ┌─────────────────────────────────────────────────────────────┐
  │  SIDEBAR (app.py)                                           │
  │  User inputs tickers, date range, benchmark                 │
  │  → yfinance.download() fetches OHLCV data                   │
  │  → Stored in st.session_state as:                           │
  │      'raw_data'   : DataFrame of daily closing prices       │
  │      'returns'    : DataFrame of daily pct_change returns   │
  │      'rf'         : float, annualised risk-free rate (^TNX) │
  │      'tickers'    : list of successfully loaded tickers     │
  │      'benchmark'  : string, e.g. 'SPY'                      │
  └─────────────────────────────────────────────────────────────┘
              │  session_state shared across all pages
              ▼
  ┌───────────┬───────────┬───────────┬───────────┬───────────┐
  │ Risk/CAPM │ Optimiz.  │ Valuation │ Rebalancer│ Adv.Models│
  │  page 1   │  page 2   │  page 3   │  page 4   │  page 5   │
  └───────────┴───────────┴───────────┴───────────┴───────────┘

SESSION STATE
  Streamlit reruns the entire script on every user interaction. Session state
  (st.session_state) acts as persistent in-memory storage between reruns and
  between pages. The data sync button populates it once; all pages read from it.
  If you navigate to a page before syncing, a warning is shown and st.stop()
  halts execution gracefully.

CACHING
  get_global_data() in app.py is decorated with @st.cache_data(ttl=3600).
  Identical (tickers, benchmark, start_date) arguments return cached data for
  up to 1 hour, avoiding redundant network calls on every rerun.

RISK-FREE RATE
  The app downloads ^TNX (US 10-Year Treasury yield) as part of the universe
  fetch. The last available value is divided by 100 to get the annualised rf.
  This is then divided by 252 inside regression loops to get a daily rf rate.

================================================================================
5. PAGE-BY-PAGE FEATURE REFERENCE
================================================================================

--------------------------------------------------------------------------------
5.1  HOME — app.py
--------------------------------------------------------------------------------

PURPOSE
  Central configuration panel and portfolio universe overview dashboard.

CONTROLS (sidebar)
  · Ticker Universe     : Comma-separated list of any Yahoo Finance symbols.
                          Supports US equities, ETFs, international stocks (e.g.
                          ASML.AS for Amsterdam, 9988.HK for Hong Kong).
  · Analysis Start Date : Historical lookback start. Earlier = more data for
                          covariance estimation but may include stale regimes.
  · Benchmark ETF       : Used as the market proxy in all CAPM and FF3
                          regressions. Default SPY; can be QQQ, URTH, EWJ, etc.
  · Sync Market Data    : Triggers yfinance download and session state population.

DASHBOARD SECTIONS
  · Universe stats table : Annualised return, annualised volatility, Sharpe ratio
                           per ticker. Colour-coded by Sharpe.
  · Correlation heatmap  : Full pairwise Pearson correlation matrix of daily
                           returns, rendered as an interactive heatmap.

--------------------------------------------------------------------------------
5.2  RISK & CAPM — pages/1_📐_Risk_&_CAPM.py
--------------------------------------------------------------------------------

PURPOSE
  Decompose each asset's return into systematic (market) and idiosyncratic
  components, analyse factor stability over time, and compute risk-adjusted
  performance metrics.

SECTION 1 — CAPM OLS Regression Table
  For each ticker, runs OLS: R_i - rf = α + β·(R_m - rf) + ε
  Outputs: Beta, Daily Alpha, Annualised Alpha, Annualised Return, R².
  Table is colour-graded by Beta (coolwarm) and Alpha (RdYlGn).

SECTION 2 — Security Market Line (SML)
  Plots the CAPM-predicted return (rf + β·ERP) as a dashed line.
  Each stock is overlaid as a scatter point coloured green (α > 0, beats CAPM)
  or red (α < 0, lags CAPM). Stocks above the SML are generating genuine
  risk-adjusted excess return; stocks below are underperforming their beta risk.

SECTION 3 — Rolling Beta
  CONTROLS:
    · Window slider   : 21–126 trading days (default 63 = ~3 months)
    · Ticker selector : Multi-select, default first 6 tickers
  CHART: Line chart of rolling beta over time with β=1 reference line.
  TABLE: Static (full-period) beta vs most recent rolling beta, delta, and a
         trend label (📈 Rising / 📉 Falling / ➡️ Stable; threshold ±0.10).
  METHOD: rolling_cov(stock, market) / rolling_var(market), pure pandas.
  WHY IT MATTERS: A stock that appears defensive at β=0.7 over 2 years may have
                  a current rolling beta of 1.3 — a hidden concentration risk.

SECTION 4 — Drawdown Analysis
  Computes the drawdown series: D_t = (P_t / max(P_1..P_t)) - 1
  Multi-select chart shows drawdown paths as filled area plots.
  Table shows max drawdown and the date it was reached per ticker.

SECTION 5 — Risk-Adjusted Metrics
  Per ticker: Annualised Return, Annualised Volatility, Sharpe Ratio,
  Sortino Ratio (downside deviation denominator), Max Drawdown, Calmar Ratio.
  Sorted by Sharpe, colour-graded.

--------------------------------------------------------------------------------
5.3  ADVANCED OPTIMIZATION ENGINE — pages/2_🎯_Optimization.py
--------------------------------------------------------------------------------

PURPOSE
  Construct the optimal portfolio from the universe using three complementary
  approaches: constrained mean-variance, risk parity, and Monte Carlo simulation.

CONTROLS
  · Max Single Asset Weight : Upper bound constraint per asset (default 20%).
  · Ledoit-Wolf toggle      : Switch between sample and shrunk covariance matrix.
  · Monte Carlo simulations : 1,000–15,000 random portfolios for frontier plot.

SECTION 1 — Constrained Max-Sharpe Portfolio
  Minimises -Sharpe using scipy.optimize.minimize with SLSQP method.
  Constraints: weights sum to 1, each weight in [0, max_w].
  Outputs: Expected Return, Volatility, Sharpe Ratio, allocation pie chart,
           weight bar chart, and weight table (weights < 0.5% filtered out).

SECTION 2 — Risk Parity Portfolio
  Finds weights where each asset contributes equally to total portfolio variance.
  Objective: minimise Σ(w_i · MRC_i - σ_p/N)² where MRC = ∂σ_p/∂w_i.
  No return forecast required — purely variance-based diversification.

SECTION 3 — Efficient Frontier (Monte Carlo)
  Triggered by button (avoids re-running on every slider change).
  Generates N random portfolios, plots return vs volatility coloured by Sharpe.
  Overlays: red star (unconstrained MC max-Sharpe), orange diamond (SLSQP result).

--------------------------------------------------------------------------------
5.4  FUNDAMENTAL VALUATION — pages/3_💰_Valuation.py
--------------------------------------------------------------------------------

PURPOSE
  Estimate the intrinsic value of each ticker using live financial statement
  data fetched directly from Yahoo Finance, then compare against market price
  to compute a margin of safety.

CONTROLS
  · DCF Growth Rate  : Stage-1 growth rate applied to free cash flow for 10 years
                       (default 8%). Terminal growth fixed at 2.5%.
  · Ticker selector  : Default first 10 tickers to limit API call time.

DATA FETCHED PER TICKER (yf.Ticker(t).info)
  marketCap, totalDebt, beta, interestExpense, freeCashflow, sharesOutstanding,
  dividendRate, sector, currentPrice.

VALUATION METHODS
  DCF (primary): 10-year explicit FCF forecast + Gordon Growth terminal value,
                 discounted at WACC. See section 6.8 for full formula.
  DDM (fallback): Used when FCF ≤ 0. Gordon Growth on dividendRate. See 6.10.

QUALITY GATE (per notebook Section 13)
  ROIC > 15% AND Interest Coverage > 5× → Quality pass (✅)
  Computed from balance sheet and income statement via yf.Ticker(t).balance_sheet
  and yf.Ticker(t).financials.

OUTPUT TABLE
  Ticker, Sector, Method (DCF/DDM), WACC, Market Price, Intrinsic Value,
  Margin of Safety, ROIC, Quality, Verdict.
  Verdict: ✅ BUY/HOLD (MoS > 15%), 🟡 FAIR VALUE (−10% < MoS < 15%),
           ⚠️ OVERVALUED (MoS < −10%).

CHARTS
  · Margin of Safety bar chart (colour scale RdYlGn, threshold line at 15%)
  · Market Price vs Intrinsic Value grouped bar chart

NOTE: Valuation page makes one yfinance API call per ticker. For large universes
(20+ stocks) expect 30–90 seconds. Results are stored in session_state so you
can re-view without re-fetching.

--------------------------------------------------------------------------------
5.5  PORTFOLIO REBALANCER — pages/4_⚖️_Rebalancer.py
--------------------------------------------------------------------------------

PURPOSE
  Given your current holdings and a target allocation, compute the exact trades
  needed to rebalance — optionally incorporating fresh capital injection.

SECTION 1 — Current Holdings (editable table)
  Displays tickers with their latest market price (auto-fetched from raw_data).
  User fills in: Shares Owned and Target Weight %.
  If target weights don't sum to 100%, they are normalised automatically with
  a warning displayed.

SECTION 2 — Cash Injection
  Fresh capital to deploy alongside the rebalance. Added to total portfolio value
  before computing target allocations.

TRADE LIST LOGIC
  For each ticker:
    current_value = last_price × shares_owned
    total_new_value = Σ(current_values) + new_cash
    target_value = total_new_value × normalised_weight
    trade_amount = target_value − current_value
    shares_to_trade = trade_amount / last_price
  Action: 🟢 BUY if diff > $1, 🔴 SELL if diff < −$1, ⚪ HOLD otherwise.

OUTPUT
  · Summary metrics: total portfolio value, cash added, total buy/sell amounts.
  · Trade list table with ticker, price, current value, target value, trade
    amount in dollars, shares to trade, and action.
  · Before/After grouped bar chart per ticker.
  · Trade action breakdown pie chart.
  · Target allocation pie chart.

--------------------------------------------------------------------------------
5.6  ADVANCED MODELS — pages/5_🔬_Advanced_Models.py
--------------------------------------------------------------------------------

Three sub-features accessed via tabs.

TAB 1 — Walk-Forward Out-of-Sample Testing
  PURPOSE: Validate that the optimizer generalises beyond the training window.
  CONTROLS:
    · Training window  : 3–12 months (default 6)
    · OOS window       : 1–6 months (default 3)
    · Max weight       : Per-asset cap during optimisation
  METHOD: Rolls a window across the return series. In each period:
    1. Train: fit max-Sharpe portfolio on training slice.
    2. Test : apply those weights to the next OOS slice.
    3. Record: OOS annualised return, volatility, Sharpe ratio.
  OUTPUT:
    · OOS Sharpe bar chart by period (colour-coded, mean line)
    · Cumulative OOS return line chart
    · Full results table

TAB 2 — Black-Litterman Optimisation
  PURPOSE: Blend market equilibrium implied returns with user views to produce
           a posterior expected return vector, then optimise on it.
  CONTROLS:
    · Number of views : 1–5
    · Per view: LONG ticker, SHORT ticker (or absolute), expected excess return %
    · τ (tau)         : Confidence parameter (lower = equilibrium dominates)
  METHOD: See section 6.12 for full mathematics.
  OUTPUT:
    · BL portfolio return and Sharpe
    · Grouped bar: Equilibrium weights vs BL optimal weights
    · Full comparison table (equilibrium returns, BL returns, both weight sets)

TAB 3 — Market Regime Detection
  PURPOSE: Identify Calm vs Stress market regimes to inform position sizing
           and hedging decisions.
  METHOD: Rolling 21-day annualised volatility of benchmark returns.
          Regimes assigned by threshold (user-adjustable slider).
          Calm: vol < threshold. Stress: vol ≥ threshold.
  OUTPUT:
    · Benchmark price chart with green/red shaded regime regions
    · Regime-conditional portfolio statistics table (return, vol, Sharpe, max DD)
    · Current regime indicator metric
    · Regime-aware optimisation: re-runs max-Sharpe using only returns from
      the current regime.

--------------------------------------------------------------------------------
5.7  FAMA-FRENCH THREE-FACTOR MODEL — pages/6_📊_Fama_French.py
--------------------------------------------------------------------------------

PURPOSE
  Extend CAPM with size (SMB) and value (HML) factors to obtain a more complete
  picture of each stock's risk exposures and genuine alpha after controlling for
  known systematic premia.

SYNTHETIC FACTOR CONSTRUCTION (from notebook Section 16)
  Because the app is fully self-contained (no external data library required):
  · Mkt-RF : benchmark daily return − daily rf
  · SMB    : equal-weight low-annual-return half of universe MINUS
             equal-weight high-annual-return half (size proxy)
  · HML    : equal-weight low-beta half MINUS equal-weight high-beta half
             (value proxy: low-beta stocks ≈ value, high-beta ≈ growth)

  NOTE: For production, replace synthetic proxies with official Ken French
  factors from https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
  using pandas_datareader (dataset: 'F-F_Research_Data_Factors_daily').
  Synthetic proxies produce qualitatively equivalent factor structure within
  a given universe.

SECTION 1 — Factor stats and correlation matrix
  Annualised mean and std dev of each factor. Factor correlation heatmap.

SECTION 2 — Three-Factor Regression Results
  OLS per ticker: R_i - rf = α₃F + β_MKT·(Mkt-RF) + β_SMB·SMB + β_HML·HML + ε
  All parameters annualised where appropriate. Alpha significance stars included
  (*** p<0.01, ** p<0.05, * p<0.10).

SECTION 3 — Factor Loading Charts
  Three horizontal bar charts (β_MKT, β_SMB, β_HML), sorted and colour-coded.
  Presented as separate tabs to avoid visual clutter.

SECTION 4 — R² Improvement: CAPM → 3F
  Side-by-side grouped bar showing how much additional variance is explained by
  adding SMB and HML. Summary: average ΔR², biggest beneficiary, count of
  stocks where 3F outperforms.

SECTION 5 — Alpha Comparison
  CAPM alpha vs 3-factor alpha per stock. Stocks where 3F alpha < CAPM alpha
  were being credited for factor exposure (size/value tilts), not genuine excess
  return skill.

================================================================================
6. MATHEMATICAL REFERENCE
================================================================================

--------------------------------------------------------------------------------
6.1  CAPM & Alpha
--------------------------------------------------------------------------------

  E[R_i] = rf + β_i · (E[R_m] − rf)

  β_i  = Cov(R_i, R_m) / Var(R_m)        (full-period OLS estimate)

  α_i  = R_i − E[R_i]                     (Jensen's Alpha, annualised × 252)

  OLS regression form:
    R_i,t − rf = α_i + β_i · (R_m,t − rf) + ε_i,t

--------------------------------------------------------------------------------
6.2  Rolling Beta
--------------------------------------------------------------------------------

  β_i,t(w) = Cov_w(R_i, R_m) / Var_w(R_m)

  where the subscript w denotes a rolling window of w trading days.
  Implemented as: rolling_cov / rolling_var using pandas rolling methods.

--------------------------------------------------------------------------------
6.3  Sharpe, Sortino & Calmar Ratios
--------------------------------------------------------------------------------

  Sharpe  = (R_p − rf) / σ_p              (annualised)

  Sortino = (R_p − rf) / σ_downside       where σ_downside = std(R_t | R_t < 0) · √252

  Calmar  = R_p / |MaxDrawdown|

  MaxDrawdown = min_t [ P_t / max_{s≤t}(P_s) − 1 ]

--------------------------------------------------------------------------------
6.4  Ledoit-Wolf Covariance Shrinkage
--------------------------------------------------------------------------------

  Σ_shrunk = (1 − δ) · Σ_sample + δ · μ · I

  where δ is the analytically optimal shrinkage intensity (computed by
  sklearn.covariance.LedoitWolf) and μ is the mean eigenvalue of Σ_sample.

  Purpose: The sample covariance matrix is ill-conditioned when N (assets) is
  large relative to T (observations). Shrinkage pulls extreme eigenvalues toward
  the mean, producing a more invertible, regularised estimate that reduces
  optimiser sensitivity to estimation error.

  The app displays: shrinkage coefficient δ and the condition number improvement
  ratio (cond(Σ_sample) / cond(Σ_shrunk)).

--------------------------------------------------------------------------------
6.5  Max-Sharpe Optimisation (SLSQP)
--------------------------------------------------------------------------------

  Maximise:  S(w) = (w'μ − rf) / √(w'Σw)

  Subject to: Σw_i = 1
              0 ≤ w_i ≤ w_max   for all i

  Implemented via scipy.optimize.minimize with method='SLSQP'
  (Sequential Least Squares Programming — handles nonlinear objectives with
  linear equality and bound constraints).

  Initial guess: equal-weight portfolio (1/N per asset).

--------------------------------------------------------------------------------
6.6  Risk Parity
--------------------------------------------------------------------------------

  Target: each asset contributes equally to total portfolio variance.

  Risk Contribution of asset i:
    RC_i = w_i · (∂σ_p / ∂w_i) = w_i · (Σw)_i / σ_p

  Objective (minimised):
    Σ_i (RC_i − σ_p / N)²

  No expected return input required. Diversification is achieved purely by
  equalising variance contributions.

--------------------------------------------------------------------------------
6.7  Monte Carlo Efficient Frontier
--------------------------------------------------------------------------------

  For each of N simulations:
    1. Draw w from Dirichlet(1,...,1) ≡ uniform random weights summing to 1.
    2. Compute: R_p = w'μ,  σ_p = √(w'Σw),  S = (R_p − rf) / σ_p
    3. Store (σ_p, R_p, S).

  Plot: scatter of (σ_p, R_p) coloured by Sharpe. The upper envelope of the
  cloud approximates the efficient frontier.

--------------------------------------------------------------------------------
6.8  DCF Valuation
--------------------------------------------------------------------------------

  Stage 1 (explicit forecast, years 1–10):
    FCF_t = FCF_0 · (1 + g)^t
    PV(FCF) = Σ_{t=1}^{10} FCF_t / (1 + WACC)^t

  Terminal Value (Gordon Growth):
    TV = FCF_10 · (1 + g_T) / (WACC − g_T)
    PV(TV) = TV / (1 + WACC)^10

  Intrinsic Value per share:
    V = (PV(FCF) + PV(TV)) / shares_outstanding

  Parameters:
    g     = user-controlled growth rate (default 8%)
    g_T   = terminal growth rate (fixed 2.5%)
    WACC  = computed per-ticker (see 6.9)

--------------------------------------------------------------------------------
6.9  WACC
--------------------------------------------------------------------------------

  WACC = (E/V) · k_e + (D/V) · k_d · (1 − tax)

  k_e   = rf + β · ERP           (CAPM cost of equity, ERP = 5.11%)
  k_d   = |Interest Expense| / Total Debt   (or rf + 2% if no debt)
  E     = marketCap
  D     = totalDebt
  V     = E + D
  tax   = 21% (US corporate flat rate)

  Floor: WACC ≥ rf (prevents pathological cases where k_d < rf)

--------------------------------------------------------------------------------
6.10  Dividend Discount Model (DDM)
--------------------------------------------------------------------------------

  Applied when FCF ≤ 0 (negative or zero free cash flow):

  V = D₁ / (k_e − g)

  where D₁ = current annualised dividendRate (from Yahoo Finance info)
        k_e = WACC (used as cost of equity proxy)
        g   = 2.5% (terminal growth)

  Returns None if k_e ≤ g or dividendRate = 0.

--------------------------------------------------------------------------------
6.11  Walk-Forward Testing
--------------------------------------------------------------------------------

  For each rolling window starting at position i:
    Train slice  : returns[i − train_days : i]
    OOS slice    : returns[i : i + oos_days]
    1. Fit max-Sharpe portfolio on train slice.
    2. Apply weights to OOS slice → daily OOS returns.
    3. Compute OOS annualised return, volatility, Sharpe.
    4. Advance i by oos_days. Repeat.

  This is an anchored rolling walk-forward (train window size is fixed, not
  expanding). It penalises strategies that overfit to a specific historical period.

--------------------------------------------------------------------------------
6.12  Black-Litterman Model
--------------------------------------------------------------------------------

  STEP 1 — Equilibrium implied returns (reverse optimisation):
    π = δ · Σ · w_eq
    where δ = risk aversion coefficient (2.5), w_eq = equal-weight market proxy.

  STEP 2 — Views:
    P · μ = Q + ε,   ε ~ N(0, Ω)
    P = views matrix (k × N), Q = view returns vector (k × 1)
    Ω = diag(τ · P · Σ · P') — uncertainty proportional to factor variance

  STEP 3 — Posterior expected return (BL combined estimate):
    μ_BL = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ · [(τΣ)⁻¹π + P'Ω⁻¹Q]

  STEP 4 — Posterior covariance:
    Σ_BL = Σ + [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹

  STEP 5 — Optimise max-Sharpe using μ_BL and Σ_BL.

  τ (user-adjustable): smaller τ → more weight on equilibrium, less on views.

--------------------------------------------------------------------------------
6.13  Regime Detection
--------------------------------------------------------------------------------

  Rolling annualised volatility:
    σ_t(21) = std(R_{t-20:t}) · √252

  Regime assignment:
    Calm   if σ_t(21) < threshold
    Stress if σ_t(21) ≥ threshold

  Threshold is user-adjustable (slider between Q25 and Q90 of the vol series).
  Default: median rolling volatility.

  This is a transparent, interpretable proxy for Hidden Markov Models (HMM),
  which are covered in the original notebook (Section 18). For a full HMM
  implementation, the hmmlearn library would replace the threshold rule.

--------------------------------------------------------------------------------
6.14  Fama-French Three-Factor Model
--------------------------------------------------------------------------------

  Regression per asset:
    R_i,t − rf = α₃F + β_MKT·(R_m,t − rf) + β_SMB·SMB_t + β_HML·HML_t + ε_i,t

  Synthetic factor construction:
    Universe sorted by annualised return → bottom half (L), top half (H)
    SMB = mean(R_L) − mean(R_H)      (small/struggling minus large/growing)

    Universe sorted by beta → bottom half (low-β), top half (high-β)
    HML = mean(R_low-β) − mean(R_high-β)   (value proxy minus growth proxy)

  Alpha interpretation:
    α₃F < α_CAPM → stock's apparent CAPM alpha was partially explained by
                   factor tilts (size or value exposure), not genuine skill.
    α₃F > 0 and statistically significant → genuine multi-factor outperformance.

================================================================================
7. DATA SOURCES & REFRESH POLICY
================================================================================

  SOURCE          : Yahoo Finance (via yfinance library)
  PRICE DATA      : Adjusted closing prices (splits and dividends accounted for)
  REFRESH         : @st.cache_data(ttl=3600) — cached for 1 hour per session.
                    Click "Sync Market Data" again to force a refresh.
  RISK-FREE RATE  : ^TNX (US 10-Year Treasury constant maturity yield).
                    Used as the annualised risk-free rate in all calculations.
  FUNDAMENTALS    : yf.Ticker(t).info, .balance_sheet, .financials — fetched
                    live on the Valuation page, not cached.
  COVERAGE        : yfinance supports US equities, ETFs, indices, and many
                    international exchanges. Use local suffixes for non-US:
                    .L (London), .PA (Paris), .AS (Amsterdam), .HK (Hong Kong), etc.
  LIMITATIONS     : Free tier; rate limits apply for very large universes.
                    Some fields (balance_sheet, freeCashflow) may be unavailable
                    for smaller or foreign-listed companies.

================================================================================
8. KNOWN LIMITATIONS & ASSUMPTIONS
================================================================================

  · All returns are based on daily adjusted closing prices. Intraday liquidity
    and bid-ask spread effects are not modelled.

  · Expected returns used in optimisation are simple historical sample means.
    These are noisy estimates — the Ledoit-Wolf shrinkage addresses covariance
    noise but not mean estimation error.

  · WACC uses a flat 21% US corporate tax rate. Non-US companies may differ
    significantly.

  · Synthetic FF3 factors are universe-specific. Results are not directly
    comparable to regressions using official Ken French factors.

  · The regime detection model uses a hard threshold on rolling volatility.
    It will lag true regime transitions by up to the window length (21 days).

  · Walk-forward results are sensitive to the choice of training window. Short
    windows may produce noisy or overfitted weights; long windows may miss
    structural breaks.

  · Valuation (DCF/DDM) outputs are highly sensitive to growth rate and WACC.
    A 1pp change in WACC can move intrinsic value by 15–30%. Use as a range
    estimate, not a precise target.

  · The app has no authentication layer. Do not deploy publicly without adding
    Streamlit authentication or a reverse proxy with access control.

================================================================================
9. EXTENDING THE APP
================================================================================

ADDING A NEW PAGE
  Create pages/7_<emoji>_<Name>.py. It will appear in the sidebar automatically.
  Access shared data via:
    returns   = st.session_state['returns']
    tickers   = st.session_state['tickers']
    raw_data  = st.session_state['raw_data']
    rf        = st.session_state['rf']
    benchmark = st.session_state['benchmark']

ADDING OFFICIAL FF3 FACTORS (replaces synthetic proxies)
  Install: pip install pandas-datareader
  Fetch:
    import pandas_datareader.data as web
    ff = web.DataReader('F-F_Research_Data_Factors_daily', 'famafrench',
                        start=start_date)[0] / 100
    ff.index = pd.to_datetime(ff.index, format='%Y%m%d')
  Align with returns by date index inner join before running OLS.

ADDING HMM REGIME DETECTION (replaces threshold model)
  Install: pip install hmmlearn
  Example:
    from hmmlearn.hmm import GaussianHMM
    model = GaussianHMM(n_components=2, covariance_type='full', n_iter=100)
    model.fit(returns_array.reshape(-1, 1))
    regimes = model.predict(returns_array.reshape(-1, 1))

DEPLOYING TO STREAMLIT CLOUD
  1. Push repository to GitHub (public or private).
  2. Go to https://share.streamlit.io → New app → select repo and app.py.
  3. Add secrets if needed via the Streamlit Cloud secrets manager.
  4. requirements.txt is picked up automatically.

================================================================================
10. DISCLAIMER
================================================================================

  This software is provided for educational and research purposes only.
  Nothing in this application constitutes financial advice, investment
  recommendations, or an offer to buy or sell any security.

  All models, valuations, and optimisation outputs are based on historical data
  and mathematical assumptions that may not reflect future market conditions.
  Past performance is not indicative of future results.

  The author accepts no liability for any financial decisions made on the basis
  of this tool. Always conduct your own due diligence and consult a qualified
  financial advisor before making investment decisions.

================================================================================
  END OF README
================================================================================
