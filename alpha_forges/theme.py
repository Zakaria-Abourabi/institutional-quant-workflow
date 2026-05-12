"""
theme.py — Alpha Forge Pro shared theming utility.
Import at the top of every page:

    from theme import apply_theme, plotly_layout

apply_theme()  injects the CSS stylesheet into the page.
plotly_layout(**overrides)  returns a consistent dark Plotly layout dict.
"""

import streamlit as st
import os

# ── Colour palette (mirrors style.css variables) ──────────────
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
SCALE_GREEN   = [[0, "#0E1117"], [1, EMERALD]]
SCALE_GOLD    = [[0, "#0E1117"], [1, GOLD]]
SCALE_DIVERG  = [[0, RED], [0.5, BG_RAISED], [1, EMERALD]]   # red → neutral → emerald


def apply_theme():
    """Inject the custom CSS stylesheet. Call once per page."""
    css_path = os.path.join(os.path.dirname(__file__), ".streamlit", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


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
            x    = 0.02,
            xanchor = "left",
        ),
        xaxis = dict(
            gridcolor      = "rgba(255,255,255,0.05)",
            linecolor      = "rgba(255,255,255,0.10)",
            tickcolor      = "rgba(255,255,255,0.10)",
            tickfont       = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_MUTED),
            title_font     = dict(family="IBM Plex Sans, sans-serif", size=11, color=TEXT_MUTED),
            showgrid       = True,
            zeroline       = False,
        ),
        yaxis = dict(
            gridcolor      = "rgba(255,255,255,0.05)",
            linecolor      = "rgba(255,255,255,0.10)",
            tickcolor      = "rgba(255,255,255,0.10)",
            tickfont       = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_MUTED),
            title_font     = dict(family="IBM Plex Sans, sans-serif", size=11, color=TEXT_MUTED),
            showgrid       = True,
            zeroline       = False,
        ),
        legend = dict(
            bgcolor       = "rgba(26,31,46,0.8)",
            bordercolor   = "rgba(255,255,255,0.08)",
            borderwidth   = 1,
            font          = dict(family="IBM Plex Mono, monospace", size=10, color=TEXT_PRIMARY),
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
