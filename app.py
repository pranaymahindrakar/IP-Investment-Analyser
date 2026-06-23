"""Counterpoint — view one company through the lens of another.

Enter a Target ticker (and optionally a Lens ticker) for AI-assisted, web-grounded
briefs, a strategic "through the lens" analysis, and a chat to dig deeper.
Data: yfinance (free). Brain: configurable LLM (Gemini now).
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from perspective import analysis, chat, data_yf, ui
from perspective.providers import get_llm

st.set_page_config(
    page_title="Counterpoint — Investment Analyzer",
    page_icon=":material/compare_arrows:",
    layout="wide",
)
ui.inject_styles()


# --------------------------------------------------------------------------- #
# Cached resources / data
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def get_llm_cached():
    return get_llm(st.secrets)


@st.cache_data(show_spinner=False, ttl=3600)
def snapshot(ticker: str):
    return data_yf.get_snapshot(ticker)


@st.cache_data(show_spinner=False, ttl=3600)
def price(ticker: str, period: str):
    return data_yf.get_price_history(ticker, period)


@st.cache_data(show_spinner=False, ttl=1800)
def brief(ticker: str, _llm):
    return analysis.company_brief(_llm, snapshot(ticker))


@st.cache_data(show_spinner=False, ttl=1800)
def lens_analysis(target: str, lens: str, _llm):
    return analysis.through_the_lens(_llm, snapshot(target), snapshot(lens))


# --------------------------------------------------------------------------- #
# UI helpers
# --------------------------------------------------------------------------- #
def render_profile(snap: dict, alt: bool = False):
    ui.company_header(snap["profile"], alt=alt)

    stats = snap["key_stats"]
    cols = st.columns(4)
    for col, label in zip(cols, ["Market cap", "Revenue (ttm)", "Profit margin", "P/E (trailing)"]):
        col.metric(label, stats.get(label) or "—")

    if snap["profile"].get("summary"):
        with st.expander("Business summary"):
            st.write(snap["profile"]["summary"])

    with st.expander("All metrics"):
        import pandas as pd

        rows = [(k, str(v)) for k, v in stats.items() if v is not None]
        if rows:
            st.table(pd.DataFrame(rows, columns=["Metric", "Value"]).set_index("Metric"))
        p = snap["profile"]
        extras = []
        if p.get("employees"):
            extras.append(f"Employees: {p['employees']:,}")
        if p.get("website"):
            extras.append(f"[{p['website']}]({p['website']})")
        if extras:
            st.caption(" · ".join(extras))


def price_chart(ticker: str, period: str, color: str):
    df = price(ticker, period)
    if df.empty:
        st.caption("No price history available.")
        return
    fig = go.Figure(go.Scatter(x=df[df.columns[0]], y=df["Close"], mode="lines"))
    st.plotly_chart(ui.style_price(fig, color), width="stretch")


def comparison_chart(target: str, lens: str, period: str):
    dt, dl = price(target, period), price(lens, period)
    if dt.empty or dl.empty:
        return
    fig = go.Figure()
    for tk, df, color in ((target, dt, ui.ACCENT), (lens, dl, ui.ACCENT_2)):
        norm = df["Close"] / df["Close"].iloc[0] * 100
        fig.add_trace(go.Scatter(x=df[df.columns[0]], y=norm, mode="lines",
                                 name=tk, line=dict(color=color, width=2)))
    st.plotly_chart(ui.style_compare(fig), width="stretch")


def render_news(snap: dict):
    news = snap.get("news") or []
    if not news:
        return
    with st.expander("Latest headlines"):
        for n in news:
            if n["url"]:
                st.markdown(f"- [{n['title']}]({n['url']}) — _{n['publisher']}_")
            else:
                st.markdown(f"- {n['title']} — _{n['publisher']}_")


# --------------------------------------------------------------------------- #
# Header + inputs
# --------------------------------------------------------------------------- #
ui.masthead()

with st.sidebar:
    st.header("About")
    st.write(
        "Pull any stock for a web-grounded brief — core business, recent news, "
        "accomplishments, and goals — then analyze it from another company's "
        "strategic perspective."
    )
    try:
        st.caption(f"AI provider: **{get_llm_cached().name}**")
    except Exception as e:  # noqa: BLE001
        st.error(f"LLM not configured: {e}")
    st.caption("Data: Yahoo Finance. Not investment advice.")

with st.form("tickers"):
    c1, c2, c3 = st.columns([3, 3, 2])
    target_in = c1.text_input("Target ticker", placeholder="e.g. NVDA", key="target_in")
    lens_in = c2.text_input("Lens ticker (optional)", placeholder="e.g. MSFT", key="lens_in")
    period = c3.selectbox("Price window", ["6mo", "1y", "2y", "5y"], index=1)
    submitted = st.form_submit_button("Analyze", type="primary", width="stretch")

if submitted:
    st.session_state["target"] = (target_in or "").strip().upper()
    st.session_state["lens"] = (lens_in or "").strip().upper()
    st.session_state["period"] = period
    st.session_state["chat_history"] = []

target = st.session_state.get("target", "")
lens = st.session_state.get("lens", "")
period = st.session_state.get("period", "1y")

if not target:
    st.info("Enter a Target ticker above and press **Analyze** to begin.")
    st.stop()

# --------------------------------------------------------------------------- #
# Load + validate
# --------------------------------------------------------------------------- #
with st.spinner(f"Loading {target}…"):
    t_snap = snapshot(target)
if not t_snap.get("valid"):
    st.error(f"Couldn't find data for **{target}**. Check the ticker symbol.")
    st.stop()

l_snap = None
if lens:
    with st.spinner(f"Loading {lens}…"):
        l_snap = snapshot(lens)
    if not l_snap.get("valid"):
        st.warning(f"Couldn't find data for Lens ticker **{lens}** — showing Target only.")
        l_snap = None
        lens = ""

try:
    llm = get_llm_cached()
except Exception as e:  # noqa: BLE001
    st.error(f"AI provider not available: {e}")
    st.stop()

# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #
if l_snap:
    ui.section("Companies", "adjust")
    pc1, pc2 = st.columns(2, gap="large")
    with pc1:
        render_profile(t_snap)
        price_chart(target, period, ui.ACCENT)
        render_news(t_snap)
    with pc2:
        render_profile(l_snap, alt=True)
        price_chart(lens, period, ui.ACCENT_2)
        render_news(l_snap)

    ui.section("Relative performance", "show_chart", "Indexed to 100 at window start")
    comparison_chart(target, lens, period)
else:
    ui.section("Company", "business")
    render_profile(t_snap)
    price_chart(target, period, ui.ACCENT)
    render_news(t_snap)

# --------------------------------------------------------------------------- #
# AI briefs
# --------------------------------------------------------------------------- #
ui.section("Briefs", "article", "Business, recent news, accomplishments, goals")
brief_cols = st.columns(2, gap="large") if l_snap else [st.container()]
with brief_cols[0]:
    if l_snap:
        st.markdown(f"**{t_snap['profile']['name']}**")
    with st.spinner("Researching…"):
        try:
            st.markdown(brief(target, llm))
        except Exception as e:  # noqa: BLE001
            st.error(f"Brief failed: {e}")
if l_snap:
    with brief_cols[1]:
        st.markdown(f"**{l_snap['profile']['name']}**")
        with st.spinner("Researching…"):
            try:
                st.markdown(brief(lens, llm))
            except Exception as e:  # noqa: BLE001
                st.error(f"Brief failed: {e}")

# --------------------------------------------------------------------------- #
# Through the lens
# --------------------------------------------------------------------------- #
if l_snap:
    ui.section(
        f"{t_snap['profile']['name']} through the lens of {l_snap['profile']['name']}",
        "compare_arrows",
    )
    with st.spinner("Analyzing…"):
        try:
            st.markdown(lens_analysis(target, lens, llm))
        except Exception as e:  # noqa: BLE001
            st.error(f"Analysis failed: {e}")

# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
ui.section("Ask a question", "forum")

context = data_yf.snapshot_to_text(t_snap)
if l_snap:
    context += "\n\n--- LENS COMPANY ---\n" + data_yf.snapshot_to_text(l_snap)

history = st.session_state.setdefault("chat_history", [])
for turn in history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

if q := st.chat_input("e.g. Could the lens company realistically afford to acquire the target?"):
    history.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                a = chat.answer(llm, context, q, history[:-1])
            except Exception as e:  # noqa: BLE001
                a = f"Sorry — that failed: {e}"
        st.markdown(a)
    history.append({"role": "assistant", "content": a})
