"""
theme.py — Alpha Forge Pro shared theming utility.
Import at the top of every page:

    from theme import apply_theme, plotly_layout

apply_theme()  injects the CSS stylesheet into the page.
plotly_layout(**overrides)  returns a consistent dark Plotly layout dict.
"""

import streamlit as st

# ── Colour palette ─────────────────────────────────────────────
EMERALD      = "#00C896"
EMERALD_DIM  = "#00916D"
GOLD         = "#C9A84C"
BG_BASE      = "#0E1117"
BG_SURFACE   = "#1A1F2E"
BG_RAISED    = "#242938"
TEXT_PRIMARY = "#F5F0E8"
TEXT_MUTED   = "#6B7A94"
RED          = "#FF5B5B"

# Sequential / diverging scales that match the palette
SCALE_GREEN  = [[0, "#0E1117"], [1, EMERALD]]
SCALE_GOLD   = [[0, "#0E1117"], [1, GOLD]]
SCALE_DIVERG = [[0, RED], [0.5, BG_RAISED], [1, EMERALD]]

# ── Embedded CSS (no file dependency) ─────────────────────────
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&display=swap');

/* ── Base & background ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0E1117 !important;
    color: #F5F0E8 !important;
}
[data-testid="stSidebar"] {
    background-color: #1A1F2E !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: #F5F0E8 !important;
    font-weight: 400 !important;
}
p, li, label, span, div {
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #F5F0E8;
}
code, pre, [data-testid="stCode"] * {
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #1A1F2E !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 6px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #00C896 !important;
    font-size: 1.4rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #6B7A94 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.10em !important;
    text-transform: uppercase !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    font-family: 'IBM Plex Mono', monospace !important;
    background: transparent !important;
    border: 1px solid rgba(0,200,150,0.45) !important;
    color: #00C896 !important;
    border-radius: 3px !important;
    letter-spacing: 0.06em !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stButton"] > button:hover {
    background: rgba(0,200,150,0.10) !important;
    border-color: #00C896 !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(0,200,150,0.15) !important;
    border-color: #00C896 !important;
    color: #00C896 !important;
    font-weight: 500 !important;
}

/* ── Inputs & selects ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: #242938 !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 4px !important;
    color: #F5F0E8 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(0,200,150,0.50) !important;
    box-shadow: 0 0 0 2px rgba(0,200,150,0.12) !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div > div {
    background: #00C896 !important;
}
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #00C896 !important;
}

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}
.dvn-scroller { background: #1A1F2E !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    color: #6B7A94 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #00C896 !important;
    border-bottom-color: #00C896 !important;
}

/* ── Info / warning / error boxes ── */
[data-testid="stAlert"] {
    background: #1A1F2E !important;
    border-left-color: #00C896 !important;
    border-radius: 4px !important;
}

/* ── Sidebar nav items ── */
[data-testid="stSidebarNav"] a {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #6B7A94 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] [aria-selected="true"] {
    color: #00C896 !important;
    background: rgba(0,200,150,0.08) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #1A1F2E !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #C9A84C !important;
    font-size: 0.82rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0E1117; }
::-webkit-scrollbar-thumb { background: #242938; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00C896; }

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00916D, #00C896) !important;
}

/* ── Plotly chart container ── */
[data-testid="stPlotlyChart"] {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden !important; }
"""


def apply_theme():
    """Inject the Alpha Forge Pro CSS. Call once at the top of every page."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def plotly_layout(**overrides) -> dict:
    """
    Return a base Plotly layout dict styled for the Alpha Forge dark theme.
    Pass keyword overrides to customise per-chart (e.g. title, height, xaxis_title).
    """
    base = dict(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = BG_SURFACE,
        font = dict(
            family = "IBM Plex Mono, monospace",
            color  = TEXT_PRIMARY,
            size   = 11,
        ),
        title = dict(
            font = dict(
                family = "DM Serif Display, serif",
                color  = TEXT_PRIMARY,
                size   = 16,
            ),
            x       = 0.02,
            xanchor = "left",
        ),
        xaxis = dict(
            gridcolor  = "rgba(255,255,255,0.05)",
            linecolor  = "rgba(255,255,255,0.10)",
            tickcolor  = "rgba(255,255,255,0.10)",
            tickfont   = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_MUTED),
            title_font = dict(family="IBM Plex Sans, sans-serif", size=11, color=TEXT_MUTED),
            showgrid   = True,
            zeroline   = False,
        ),
        yaxis = dict(
            gridcolor  = "rgba(255,255,255,0.05)",
            linecolor  = "rgba(255,255,255,0.10)",
            tickcolor  = "rgba(255,255,255,0.10)",
            tickfont   = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_MUTED),
            title_font = dict(family="IBM Plex Sans, sans-serif", size=11, color=TEXT_MUTED),
            showgrid   = True,
            zeroline   = False,
        ),
        legend = dict(
            bgcolor     = "rgba(26,31,46,0.8)",
            bordercolor = "rgba(255,255,255,0.08)",
            borderwidth = 1,
            font        = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_PRIMARY),
        ),
        margin   = dict(l=48, r=24, t=56, b=48),
        height   = 460,
        hoverlabel = dict(
            bgcolor    = BG_RAISED,
            bordercolor= EMERALD,
            font       = dict(family="IBM Plex Mono, monospace", size=11, color=TEXT_PRIMARY),
        ),
        colorway = [EMERALD, GOLD, "#5B8CFF", "#FF7B5B", "#B55BFF",
                    "#5BFFDE", "#FFD45B", "#FF5B8C"],
    )
    # Merge overrides (supports nested dicts one level deep)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base
