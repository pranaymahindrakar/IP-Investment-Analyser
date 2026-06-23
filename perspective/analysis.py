"""Prompt builders for the two AI outputs: a company brief and the lens analysis."""

from __future__ import annotations

from typing import Any

from .data_yf import snapshot_to_text
from .providers.base import LLMProvider

_SYSTEM = (
    "You are a sharp, plain-spoken equity research analyst. Be concrete and "
    "specific, avoid hype and hedging, and never invent numbers. When you use "
    "web information, prefer recent, reputable sources. Format with short "
    "Markdown sections and tight bullet points."
)


def company_brief(llm: LLMProvider, snapshot: dict[str, Any]) -> str:
    """Recent news, accomplishments, and stated goals for one company (web-grounded)."""
    name = snapshot["profile"]["name"]
    ticker = snapshot["profile"]["ticker"]
    prompt = f"""Research {name} ({ticker}) and write a current brief.

Here is structured reference data (do not contradict it):
{snapshot_to_text(snapshot)}

Write these Markdown sections:
### What they actually do
2-3 sentences on the core business and how it makes money.
### Recent news (last ~6 months)
4-6 bullets of concrete, dated developments.
### Recent accomplishments
3-5 bullets of wins: launches, milestones, financial beats, deals.
### Stated goals & strategy
3-5 bullets on where management says they're headed.

Keep the whole thing under ~400 words."""
    return llm.generate(prompt, system=_SYSTEM, use_search=True)


def through_the_lens(
    llm: LLMProvider, target: dict[str, Any], lens: dict[str, Any]
) -> str:
    """Analyze the TARGET company from the strategic perspective of the LENS company."""
    t = target["profile"]["name"]
    l = lens["profile"]["name"]
    prompt = f"""Analyze **{t}** strictly from the perspective of **{l}** — i.e. how
{l}'s leadership, strategy, and capital would view {t} as a target, partner, competitor,
or investment.

TARGET company ({t}):
{snapshot_to_text(target)}

LENS company ({l}) — the viewpoint:
{snapshot_to_text(lens)}

Write these Markdown sections:
### Strategic fit
How {t} aligns (or clashes) with {l}'s business and direction.
### Deal-making angle
Could {l} realistically acquire, partner with, or invest in {t}? Affordability vs.
{l}'s size/cash, likely structure, and obvious blockers.
### Overlap & concentration
Where the two overlap (markets, customers, products) and any concentration risk.
### Investment opportunity
The bull case and bear case for {l} engaging with {t}, in plain terms.
### Key risks
3-5 bullets on what could go wrong from {l}'s standpoint.
### Bottom line
2-3 sentence verdict.

Be specific to these two companies. Use web info for anything recent. Under ~500 words."""
    return llm.generate(prompt, system=_SYSTEM, use_search=True)


SCORECARD_DIMENSIONS = [
    "Strategic fit",
    "Acquisition affordability",
    "Synergy potential",
    "Growth outlook",
    "Financial strength",
    "Risk-adjusted appeal",
]


def scorecard(llm: LLMProvider, target: dict[str, Any], lens: dict[str, Any]) -> dict[str, Any]:
    """Rate the TARGET from the LENS company's perspective, 0-100 per dimension.

    Returns {"dimensions": [{"name","score","rationale"}], "overall": int, "verdict": str}.
    Scores are clamped to 0-100 and missing dimensions backfilled so the UI stays stable.
    """
    t = target["profile"]["name"]
    l = lens["profile"]["name"]
    dims = ", ".join(SCORECARD_DIMENSIONS)
    prompt = f"""Score **{t}** as an opportunity from **{l}**'s perspective.

Return ONLY a JSON object of this exact shape:
{{
  "dimensions": [{{"name": "<one of the dimensions>", "score": <int 0-100>, "rationale": "<=12 words"}}],
  "overall": <int 0-100>,
  "verdict": "<=22 words"
}}

Use exactly these six dimensions: {dims}.
Higher score = more attractive for {l}. For "Risk-adjusted appeal", higher = safer/more attractive.

TARGET ({t}):
{snapshot_to_text(target)}

LENS ({l}):
{snapshot_to_text(lens)}"""

    data = llm.generate_json(prompt, system=_SYSTEM)

    by_name = {d.get("name"): d for d in data.get("dimensions", []) if isinstance(d, dict)}
    dims_out = []
    for name in SCORECARD_DIMENSIONS:
        d = by_name.get(name, {})
        try:
            score = max(0, min(100, int(round(float(d.get("score"))))))
        except (TypeError, ValueError):
            score = 0
        dims_out.append({"name": name, "score": score, "rationale": d.get("rationale", "")})

    try:
        overall = max(0, min(100, int(round(float(data.get("overall"))))))
    except (TypeError, ValueError):
        overall = round(sum(d["score"] for d in dims_out) / len(dims_out)) if dims_out else 0

    return {"dimensions": dims_out, "overall": overall, "verdict": data.get("verdict", "")}
