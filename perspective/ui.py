"""Visual layer for Counterpoint: fonts, CSS, and reusable header/section helpers.

Editorial fintech look — serif masthead (Bell MT, falling back to Libre Baskerville),
Inter body, Material Symbols vector icons, company logos, and styled metric cards.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

# Palette
INK = "#17201f"
ACCENT = "#15514a"   # deep teal — Target
ACCENT_2 = "#9c5a23"  # warm bronze — Lens

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

:root{
  --cp-ink:#17201f; --cp-muted:#616c69; --cp-line:#e6e1d6;
  --cp-paper:#fcfbf8; --cp-card:#ffffff; --cp-accent:#15514a; --cp-accent2:#9c5a23;
  --cp-serif:'Bell MT','Libre Baskerville',Georgia,'Times New Roman',serif;
  --cp-sans:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif;
}

html, body, .stApp, [data-testid="stAppViewContainer"]{
  background:var(--cp-paper); color:var(--cp-ink); font-family:var(--cp-sans);
}
#MainMenu, footer, [data-testid="stDecoration"]{visibility:hidden;}
[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:2.1rem; max-width:1180px;}

h1,h2,h3,h4{font-family:var(--cp-serif); color:var(--cp-ink); letter-spacing:.2px;}
.stMarkdown, .stMarkdown p, .stMarkdown li, label, p{font-family:var(--cp-sans);}
.stMarkdown h3{font-size:1.12rem; margin:.7rem 0 .25rem; font-weight:700;}

/* masthead */
.cp-wordmark{font-family:var(--cp-serif); font-size:3rem; font-weight:700; line-height:1.04; letter-spacing:.4px;}
.cp-wordmark .dot{color:var(--cp-accent);}
.cp-tagline{font-family:var(--cp-sans); color:var(--cp-muted); font-size:1.03rem; margin-top:.4rem; max-width:680px;}
.cp-rule{height:1px; background:linear-gradient(90deg,var(--cp-line),rgba(230,225,214,0)); margin:1.15rem 0 .2rem;}

/* section header */
.cp-section{display:flex; align-items:baseline; gap:.55rem; margin:1.7rem 0 .7rem;}
.cp-section .ms{font-size:1.4rem; color:var(--cp-accent); transform:translateY(.18rem);}
.cp-section .t{font-family:var(--cp-serif); font-size:1.5rem; font-weight:700;}
.cp-section .sub{font-family:var(--cp-sans); color:var(--cp-muted); font-size:.88rem;}

/* company header */
.cp-co{display:flex; align-items:center; gap:.85rem; margin:.1rem 0 .25rem;}
.cp-co img{width:48px; height:48px; border-radius:11px; object-fit:contain;
  background:#fff; border:1px solid var(--cp-line); padding:5px;}
.cp-co .nm{font-family:var(--cp-serif); font-size:1.4rem; font-weight:700; line-height:1.1;}
.cp-co .tk{font-family:var(--cp-sans); color:var(--cp-muted); font-size:.8rem; letter-spacing:1px;}
.cp-chips{margin:.15rem 0 .55rem;}
.cp-chip{display:inline-block; font-family:var(--cp-sans); font-size:.72rem; color:var(--cp-accent);
  background:rgba(21,81,74,.07); border:1px solid rgba(21,81,74,.18);
  padding:.13rem .55rem; border-radius:999px; margin-right:.35rem; margin-bottom:.2rem;}
.cp-chip.alt{color:var(--cp-accent2); background:rgba(156,90,35,.07); border-color:rgba(156,90,35,.2);}

/* metric cards */
[data-testid="stMetric"]{
  background:var(--cp-card); border:1px solid var(--cp-line); border-radius:14px;
  padding:.7rem .95rem; box-shadow:0 1px 2px rgba(20,20,20,.03);
}
[data-testid="stMetricLabel"] p{font-family:var(--cp-sans); color:var(--cp-muted); font-size:.76rem; font-weight:500;}
[data-testid="stMetricValue"]{font-family:var(--cp-serif); font-weight:700; font-size:1.45rem;}

/* material symbol utility */
.ms{font-family:'Material Symbols Outlined'; font-weight:normal; font-style:normal;
  line-height:1; -webkit-font-feature-settings:'liga'; font-feature-settings:'liga'; vertical-align:middle;}

/* form + buttons + inputs */
[data-testid="stForm"]{border:1px solid var(--cp-line); border-radius:16px;
  background:var(--cp-card); padding:1.05rem 1.15rem; box-shadow:0 1px 2px rgba(20,20,20,.03);}
.stButton>button, [data-testid="stFormSubmitButton"]>button{
  font-family:var(--cp-sans); font-weight:600; border-radius:10px;
  border:1px solid var(--cp-accent); background:var(--cp-accent); color:#fff; padding:.5rem 1.15rem;}
.stButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover{filter:brightness(1.08); color:#fff;}
[data-testid="stTextInput"] input{border-radius:10px;}

/* expander, bordered container, chat */
[data-testid="stExpander"]{border:1px solid var(--cp-line); border-radius:12px; background:var(--cp-card);}
[data-testid="stExpander"] summary p{font-family:var(--cp-sans); font-weight:500;}
[data-testid="stChatMessage"]{background:var(--cp-card); border:1px solid var(--cp-line); border-radius:12px;}
[data-testid="stSidebar"]{background:#f6f3ec; border-right:1px solid var(--cp-line);}
[data-testid="stSidebar"] h2{font-size:1.2rem;}
</style>
"""


def inject_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def masthead() -> None:
    st.markdown(
        '<div class="cp-wordmark">Counterpoint<span class="dot">.</span></div>'
        '<div class="cp-tagline">See one company through the lens of another. '
        "Enter a <b>Target</b> to analyze, and optionally a <b>Lens</b> company to view it from.</div>"
        '<div class="cp-rule"></div>',
        unsafe_allow_html=True,
    )


def section(title: str, icon: str, sub: str | None = None) -> None:
    """Editorial section header with a Material vector icon (no emoji)."""
    sub_html = f'<span class="sub">{sub}</span>' if sub else ""
    st.markdown(
        f'<div class="cp-section"><span class="ms">{icon}</span>'
        f'<span class="t">{title}</span>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def company_header(profile: dict[str, Any], alt: bool = False) -> None:
    """Logo + name + ticker + sector/industry chips."""
    logo = profile.get("logo")
    img = f'<img src="{logo}" alt="logo"/>' if logo else ""
    chip_cls = "cp-chip alt" if alt else "cp-chip"
    chips = "".join(
        f'<span class="{chip_cls}">{v}</span>'
        for v in (profile.get("sector"), profile.get("industry"))
        if v
    )
    st.markdown(
        f'<div class="cp-co">{img}<div>'
        f'<div class="nm">{profile.get("name")}</div>'
        f'<div class="tk">{profile.get("ticker")}</div></div></div>'
        f'<div class="cp-chips">{chips}</div>',
        unsafe_allow_html=True,
    )


def style_price(fig, color: str):
    """Refined area-line styling for a single-series price chart."""
    fig.update_traces(line=dict(color=color, width=2), fill="tozeroy",
                      fillcolor=_rgba(color, 0.06))
    fig.update_layout(
        template="simple_white", height=240,
        margin=dict(l=0, r=0, t=8, b=0), hovermode="x unified",
        font=dict(family="Inter, sans-serif", color=INK, size=12),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,.06)", zeroline=False, title=None),
    )
    return fig


def style_compare(fig):
    fig.update_layout(
        template="simple_white", height=320,
        margin=dict(l=0, r=0, t=8, b=0), hovermode="x unified",
        font=dict(family="Inter, sans-serif", color=INK, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,.06)", zeroline=False, title="Indexed to 100"),
    )
    return fig


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
