# Providers & keys — what council mode can actually use

A recurring confusion, stated plainly up front:

> **A ChatGPT Plus or Gemini Advanced subscription is a UI product. It does NOT include API
> access.** A script cannot log into your consumer subscription and drive the model. Programmatic
> multi-model work needs **API keys**, which are billed separately, per-token.

So "I already pay for ChatGPT and Gemini, use those" isn't available to an automated council.
Here are the options that *are*, ranked by how little setup/cost they impose.

## Option 1 — Claude subagents (no key, $0 beyond the session)

The default for council mode. Runs entirely inside this environment using diverse prompt
framings instead of different vendors. No external key, no extra bill. Limitation: it can't catch
a blind spot shared by all Claude models — that's the one thing real multi-vendor buys.

Pick this unless you specifically need different model *families*.

## Option 2 — OpenRouter (one key, one bill, all vendors)

[OpenRouter](https://openrouter.ai) proxies most major models behind a single API key and a
single invoice. This is the **one-key simplicity** option — the simplest way to get genuine
cross-vendor diversity (GPT, Gemini, Claude, and more) without juggling three billing accounts.

```bash
export OPENROUTER_API_KEY=sk-or-...
```

- Pay-per-token with a small routing markup over each provider's direct price.
- Model IDs look like `openai/gpt-5`, `google/gemini-2.5-pro`, `anthropic/claude-opus-4-8`.
  These change — check OpenRouter's live model list rather than trusting any hardcoded name.
- Used by `scripts/council.py`.

Trade-off versus direct keys: slightly higher per-token cost, in exchange for one key and one bill.
Given the goal of "simplicity of one API key to manage", this is usually the right pick.

## Option 3 — Direct vendor API keys

Most control, least convenience — one key and one bill *per vendor*:

- **OpenAI API** (`OPENAI_API_KEY`) — pay-per-token, **no free tier**.
- **Google Gemini API** (`GEMINI_API_KEY`, via Google AI Studio) — pay-per-token, **has a free
  tier** (rate-limited, but $0). If you want a no-cost real-vendor voice, a direct Gemini key is
  the way.
- **Anthropic API** (`ANTHROPIC_API_KEY`) — pay-per-token.

Direct keys avoid OpenRouter's markup but mean managing a separate account and bill for each vendor.

## Recommendation

- **Just want it to work, no setup:** Claude-subagent council (Option 1). Default.
- **Want real cross-vendor diversity with minimal hassle:** one OpenRouter key (Option 2).
- **Cost-sensitive but want a real non-Claude voice:** add a free-tier Gemini key (Option 3).

`scripts/council.py` reads `OPENROUTER_API_KEY`. To use direct keys instead, point the script's
base URL / key env at the vendor (see the script header) — but OpenRouter is the path of least
resistance and what the script assumes by default.

## Security

Keys are secrets. Set them as environment variables; never commit them. The community NotebookLM
bridges (see notebooklm.md) drive a logged-in Google session — review any such tool before
granting it your account, same as installing any software with access to your data.
