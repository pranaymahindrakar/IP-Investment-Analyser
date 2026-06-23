# 🔭 Perspective — Investment Analyzer

See one company **through the lens of another**. Pull any stock for a
web-grounded brief — core business, recent news, accomplishments, and goals —
then analyze it from another company's strategic perspective (deal-making fit,
overlap/concentration, investment opportunity, risks). Includes a chat to dig
deeper.

- **Data:** Yahoo Finance via `yfinance` (free, no key)
- **Brain:** configurable LLM — **Gemini** now, **Claude** later (one config switch)
- **UI/Hosting:** Streamlit → Streamlit Community Cloud (free shareable link)

> Not investment advice.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Secrets live in `.streamlit/secrets.toml` (gitignored). Minimum:

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "your-key"
GEMINI_MODEL = "gemini-2.5-flash"
```

Get a Gemini key at https://aistudio.google.com/apikey (keys start with `AIza`).

## Switch to Claude later

```bash
pip install anthropic
```

```toml
LLM_PROVIDER = "claude"
ANTHROPIC_API_KEY = "your-key"
CLAUDE_MODEL = "claude-opus-4-8"
```

## Deploy (shareable link)

1. Push this folder to a **GitHub** repo (`.streamlit/secrets.toml` is gitignored — it will NOT be uploaded).
2. Go to https://share.streamlit.io → **New app** → pick the repo, set main file to `app.py`.
3. In the app's **Settings → Secrets**, paste the same keys from your local `secrets.toml`.
4. Deploy → you get a public `*.streamlit.app` URL to share.

## Project layout

```
app.py                      Streamlit UI
perspective/
  data_yf.py                yfinance fetchers
  analysis.py               company brief + "through the lens" engine
  chat.py                   Q&A over loaded context
  providers/
    base.py                 LLM interface
    gemini.py               Gemini (active)
    claude.py               Claude (for later)
    lseg.py / factset.py    enterprise data adapter stubs (need paid creds)
```

### LSEG / FactSet

These require **paid enterprise API credentials + SDKs** — the Claude.ai
connectors do not work from a standalone hosted app. The adapters in
`perspective/providers/` are inert until you add real credentials to secrets and
implement their `fetch()` methods. The app runs fully on yfinance + LLM search
without them.
