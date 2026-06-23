"""Free-form Q&A grounded in the loaded company context."""

from __future__ import annotations

from .providers.base import LLMProvider

_SYSTEM = (
    "You are an equity research assistant answering questions about specific "
    "companies the user has loaded. Use the provided context first; use web "
    "search for anything recent or missing. Be concise, concrete, and honest "
    "about uncertainty. Never invent figures."
)


def answer(
    llm: LLMProvider,
    context: str,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    convo = ""
    for turn in history or []:
        role = "User" if turn["role"] == "user" else "Assistant"
        convo += f"{role}: {turn['content']}\n"

    prompt = f"""Loaded company context:
{context}

Conversation so far:
{convo or '(none)'}

New question: {question}

Answer it."""
    return llm.generate(prompt, system=_SYSTEM, use_search=True)
