"""Counterpoint — view one company through the lens of another.

Search any company, set a Target and an optional Lens, then explore AI-assisted,
web-grounded briefs, a strategic "through the lens" analysis, a rated scorecard,
and a chat. Data: yfinance (free). Brain: configurable LLM (Gemini now).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from perspective import analysis, chat, data_yf, ui
from perspective.providers import get_llm
from perspective.search import search_tickers

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


@st.cache_data(show_spinner=False, ttl=600)
def search(q: str):
    return search_tickers(q)


@st.cache_data(show_spinner=False, ttl=86400)
def ticker_logo(sym: str):
    return data_yf.logo_for_ticker(sym)


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


@st.cache_data(show_spinner=False, ttl=1800)
def scorecard(target: str, lens: str, _llm):
    return analysis.scorecard(_llm, snapshot(target), snapshot(lens))


# --------------------------------------------------------------------------- #
# Rendering helpers
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
        rows = [(k, str(v)) for k, v in stats.items() if v is not None]
        if rows:
            st.table(pd.DataFrame(rows, columns=["Metric", "Value"]).set_index("Metric"))


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


def set_pick(role: str, sym: str, name: str):
    st.session_state[f"sel_{role}"] = sym
    st.session_state[f"sel_{role}_name"] = name


# --------------------------------------------------------------------------- #
# Header + search/selection
# --------------------------------------------------------------------------- #
ui.masthead()

with st.sidebar:
    st.header("About")
    st.write(
        "Search any company, set a **Target** and an optional **Lens**, then explore "
        "web-grounded briefs, a strategic analysis, a rated scorecard, and a chat."
    )
    try:
        st.caption(f"AI provider: **{get_llm_cached().name}**")
    except Exception as e:  # noqa: BLE001
        st.error(f"LLM not configured: {e}")
    st.caption("Data: Yahoo Finance. Not investment advice.")

with st.container(border=True):
    q = st.text_input(
        "Search a company or ticker",
        placeholder="Try “apple”, “nvidia”, or a ticker like MSFT",
        key="q",
    )
    if q:
        results = search(q)
        if results:
            for r in results:
                sym, name = r["symbol"], r["name"]
                logo = ticker_logo(sym)
                c0, c1, c2, c3 = st.columns([0.7, 4.6, 1.2, 1.2], vertical_alignment="center")
                if logo:
                    c0.image(logo, width=34)
                else:
                    c0.markdown(
                        f"<div style='width:34px;height:34px;border-radius:8px;background:#efece4;"
                        f"border:1px solid #e6e1d6;display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;color:#616c69'>{sym[:1]}</div>",
                        unsafe_allow_html=True,
                    )
                c1.markdown(
                    f"**{sym}** · {name}<br><span style='color:#616c69;font-size:.78rem'>"
                    f"{r['exchange']} · {r['type']}</span>",
                    unsafe_allow_html=True,
                )
                c2.button("Target", key=f"t_{sym}", width="stretch",
                          on_click=set_pick, args=("target", sym, name))
                c3.button("Lens", key=f"l_{sym}", width="stretch",
                          on_click=set_pick, args=("lens", sym, name))
        else:
            direct = q.strip().upper()
            st.caption(f"No matches found. Use “{direct}” directly:")
            d1, d2, _ = st.columns([1.2, 1.2, 4])
            d1.button("Target", key="dt", on_click=set_pick, args=("target", direct, direct))
            d2.button("Lens", key="dl", on_click=set_pick, args=("lens", direct, direct))

    # current selections
    sel_t, sel_l = st.session_state.get("sel_target"), st.session_state.get("sel_lens")
    if sel_t or sel_l:
        st.markdown("")
        s1, s2 = st.columns(2)
        with s1:
            if sel_t:
                ui.selected_chip(
                    {"ticker": sel_t, "name": st.session_state.get("sel_target_name", sel_t),
                     "logo": ticker_logo(sel_t)}, "Target")
        with s2:
            if sel_l:
                ui.selected_chip(
                    {"ticker": sel_l, "name": st.session_state.get("sel_lens_name", sel_l),
                     "logo": ticker_logo(sel_l)}, "Lens", alt=True)

    b1, b2, b3 = st.columns([2, 2, 2])
    period = b1.selectbox("Price window", ["6mo", "1y", "2y", "5y"], index=1)
    analyze = b2.button("Analyze", type="primary", width="stretch", disabled=not sel_t)
    if b3.button("Clear", width="stretch"):
        for k in ("sel_target", "sel_lens", "sel_target_name", "sel_lens_name", "go",
                  "active_target", "active_lens"):
            st.session_state.pop(k, None)
        st.rerun()

if analyze:
    st.session_state["active_target"] = sel_t
    st.session_state["active_lens"] = sel_l or ""
    st.session_state["period"] = period
    st.session_state["go"] = True
    st.session_state["chat_history"] = []
    for k in ("gen_briefs", "gen_lens", "gen_score"):  # reset on-demand AI gates
        st.session_state.pop(k, None)

target = st.session_state.get("active_target", "")
lens = st.session_state.get("active_lens", "")
period = st.session_state.get("period", "1y")

if not (st.session_state.get("go") and target):
    st.info("Search a company, set it as **Target** (and optionally a **Lens**), then press **Analyze**.")
    st.stop()

# --------------------------------------------------------------------------- #
# Load + validate
# --------------------------------------------------------------------------- #
with st.spinner(f"Loading {target}…"):
    t_snap = snapshot(target)
if not t_snap.get("valid"):
    st.error(f"Couldn't find data for **{target}**. Try a different ticker.")
    st.stop()

l_snap = None
if lens:
    with st.spinner(f"Loading {lens}…"):
        l_snap = snapshot(lens)
    if not l_snap.get("valid"):
        st.warning(f"Couldn't find data for Lens **{lens}** — showing Target only.")
        l_snap = None
        lens = ""

try:
    llm = get_llm_cached()
except Exception as e:  # noqa: BLE001
    st.error(f"AI provider not available: {e}")
    st.stop()


# --------------------------------------------------------------------------- #
# Tabbed output
# --------------------------------------------------------------------------- #
def tab_overview():
    if l_snap:
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
        bars = ui.comparison_bars(
            t_snap["num"], l_snap["num"], t_snap["profile"]["name"], l_snap["profile"]["name"]
        )
        if bars is not None:
            ui.section("Fundamentals side by side", "bar_chart", "Margins & growth (%)")
            st.plotly_chart(bars, width="stretch")
    else:
        render_profile(t_snap)
        price_chart(target, period, ui.ACCENT)
        render_news(t_snap)


def tab_briefs():
    if not (st.session_state.get("gen_briefs")
            or st.button("Generate briefs", type="primary", key="btn_gen_briefs")):
        st.caption("Web-grounded brief for each company — business, news, accomplishments, goals. "
                   "Runs one AI request per company; cached after.")
        return
    st.session_state["gen_briefs"] = True
    cols = st.columns(2, gap="large") if l_snap else [st.container()]
    with cols[0]:
        if l_snap:
            st.markdown(f"**{t_snap['profile']['name']}**")
        with st.spinner("Researching…"):
            try:
                st.markdown(brief(target, llm))
            except Exception as e:  # noqa: BLE001
                st.error(f"Brief failed: {e}")
    if l_snap:
        with cols[1]:
            st.markdown(f"**{l_snap['profile']['name']}**")
            with st.spinner("Researching…"):
                try:
                    st.markdown(brief(lens, llm))
                except Exception as e:  # noqa: BLE001
                    st.error(f"Brief failed: {e}")


def tab_lens():
    if not (st.session_state.get("gen_lens")
            or st.button("Generate analysis", type="primary", key="btn_gen_lens")):
        st.caption("Strategic read of the target through the lens company — fit, deal angle, "
                   "overlap, opportunity, risks. Runs one AI request; cached after.")
        return
    st.session_state["gen_lens"] = True
    with st.spinner("Analyzing…"):
        try:
            st.markdown(lens_analysis(target, lens, llm))
        except Exception as e:  # noqa: BLE001
            st.error(f"Analysis failed: {e}")


def tab_scorecard():
    if not (st.session_state.get("gen_score")
            or st.button("Generate scorecard", type="primary", key="btn_gen_score")):
        st.caption("Rate the target across six dimensions from the lens company's viewpoint, "
                   "with an overall gauge. Runs one AI request; cached after.")
        return
    st.session_state["gen_score"] = True
    with st.spinner("Scoring…"):
        try:
            sc = scorecard(target, lens, llm)
        except Exception as e:  # noqa: BLE001
            st.error(f"Scorecard failed: {e}")
            return
    left, right = st.columns([1, 1.5], gap="large")
    with left:
        st.plotly_chart(ui.gauge(sc["overall"]), width="stretch")
        if sc.get("verdict"):
            st.markdown(f'<div class="cp-verdict">{sc["verdict"]}</div>', unsafe_allow_html=True)
    with right:
        for d in sc["dimensions"]:
            ui.score_bar(d["name"], d["score"], d.get("rationale", ""))


def tab_chat():
    context = data_yf.snapshot_to_text(t_snap)
    if l_snap:
        context += "\n\n--- LENS COMPANY ---\n" + data_yf.snapshot_to_text(l_snap)
    history = st.session_state.setdefault("chat_history", [])
    for turn in history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
    if prompt := st.chat_input("Ask anything about these companies…"):
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    ans = chat.answer(llm, context, prompt, history[:-1])
                except Exception as e:  # noqa: BLE001
                    ans = f"Sorry — that failed: {e}"
            st.markdown(ans)
        history.append({"role": "assistant", "content": ans})


if l_snap:
    names = ["Overview", "Briefs", "Lens Analysis", "Scorecard", "Q&A"]
    t_over, t_brief, t_lens, t_score, t_qa = st.tabs(names)
    with t_over:
        tab_overview()
    with t_brief:
        tab_briefs()
    with t_lens:
        ui.section(
            f"{t_snap['profile']['name']} through the lens of {l_snap['profile']['name']}",
            "compare_arrows",
        )
        tab_lens()
    with t_score:
        ui.section(
            f"Scorecard — {t_snap['profile']['name']} for {l_snap['profile']['name']}",
            "leaderboard",
        )
        tab_scorecard()
    with t_qa:
        tab_chat()
else:
    t_over, t_brief, t_qa = st.tabs(["Overview", "Brief", "Q&A"])
    with t_over:
        tab_overview()
    with t_brief:
        tab_briefs()
    with t_qa:
        tab_chat()
