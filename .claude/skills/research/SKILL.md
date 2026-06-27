---
name: research
description: Produce a deep, multi-source, cited research brief grounded in the current session's goal and context. Runs one of three modes — a web sweep (fan-out search + adversarial verification), a multi-model "council" (several models answer, anonymously cross-review, then a chairman synthesizes), or a grounded pass over a fixed source corpus via NotebookLM. Use this skill whenever the user asks to "research", "look into", "do a deep dive", "compare approaches", "find prior art", "survey the options", or wants a fact-checked report — and also call it from inside other skills (e.g. skill-creator) once a goal is set, to surface what the user wouldn't have thought to mention. Prefer this over answering open-ended factual or "which approach" questions from memory.
---

# Research

A reusable research harness. It takes **the goal and context already established in this
session** and returns a **synthesized, cited brief** — the kind of background a person would
gather by reading widely, cross-checking, and writing it up.

It is designed to be invoked two ways:

1. **Standalone** — the user says "research X" / "do a deep dive on Y". You run it directly.
2. **From inside another skill** — e.g. `skill-creator` calls it after capturing intent, to
   fill in prior art, competing approaches, the real API surface, and known gotchas that the
   user's interview didn't cover. See [references/embedding.md](references/embedding.md).

The point of running research *after a goal is set* is that the most valuable findings are the
ones **nobody thought to ask for**. The interview captures what the user knows; research
captures what they didn't know to mention.

## Step 0 — Frame the question from session context

Before searching anything, write down (briefly, to yourself):

- **Goal** — what the session is actually trying to achieve.
- **Context** — constraints already known (environment, stack, budget, deadline, audience,
  prior decisions). Pull these from the conversation; do not re-ask what's already been said.
- **Decision the research must inform** — "which approach", "is X true", "what's the prior art",
  "what will bite us". Naming this picks the mode.
- **What 'done' looks like** — the shape of the answer (a recommendation? a fact table? a list
  of risks?).

If the question is genuinely underspecified (no budget/region/use-case where those decide the
answer), ask **2–3 sharp clarifying questions first**, then proceed. Don't ask for things the
context already supplies.

## Step 1 — Pick the mode

| Mode | Engine | Use when | Needs |
|------|--------|----------|-------|
| **Web sweep** (default) | Fan-out web search + fetch + adversarial verify | Open-web facts, prior art, "is this true", surveying tools/libraries | Web access only — works out of the box |
| **Council** | Several models answer independently → anonymized peer review → chairman synthesis | Hard judgment calls, "which approach", design trade-offs, anything where one model's blind spot is a real risk | Multiple "voices" — Claude subagents (free, default) or external models via one OpenRouter key |
| **Grounded** | Q&A anchored to a fixed corpus via NotebookLM | Reasoning that must stay tied to specific sources (a spec, a paper set, internal docs) with citations and minimal hallucination | A NotebookLM bridge + Google auth |

You can **chain** modes: web-sweep to gather sources → load them into grounded mode for
citation-tight answers, or run a council *over* the brief a web-sweep produced to pressure-test
its conclusions. Default to web-sweep alone unless the decision is high-stakes or contested.

## Mode A — Web sweep (default)

This is the everyday mode and the only one that needs no setup.

1. **Decompose** the goal into 3–6 independent sub-questions. Diversity beats depth here: vary
   the *angle* (by-concept, by-vendor, by-failure-mode, by-time) so you're not just re-asking
   one query five ways.
2. **Fan out** searches across the sub-questions. If a dedicated `deep-research` skill is
   available in the session, prefer delegating to it — it already does fan-out + verification.
   Otherwise use `WebSearch`/`WebFetch` (or web-capable subagents) directly.
3. **Fetch and read** the most credible primary sources — official docs, source repos, specs,
   first-party posts — not just summaries. Capture the URL for every claim you'll rely on.
4. **Adversarially verify** load-bearing claims. For anything that would change the
   recommendation if wrong, find a second independent source, or spawn a skeptic pass prompted
   to *refute* it. Default to "unverified" when sources conflict, and say so.
5. **Synthesize** into the brief format below. Distinguish **established fact** (multiple primary
   sources) from **single-source** from **your inference**.

Quality bar: a claim that drives a decision needs a citation. If you can't cite it, label it as
inference and flag the uncertainty.

## Mode B — Council (multi-model deliberation)

Best for "which approach / is this design right" questions, where the failure mode is *one
model being confidently wrong*. Based on Karpathy's LLM Council: answer independently → review
**blind** → synthesize.

- **Default engine: Claude subagents.** Works fully inside this environment, no keys, no cost
  beyond the session. Spawn N subagents with *deliberately diverse framings* (e.g. risk-first,
  user-first, simplest-thing-that-works), have each answer independently, then run an
  anonymized cross-review, then a chairman synthesis.
- **Optional engine: real multi-vendor via OpenRouter.** One API key, one bill, genuine
  cross-vendor diversity (GPT + Gemini + Claude + …). Use when you specifically want
  *different model families* checking each other, not just different prompts.

The full procedure, the anonymized-review prompt, the chairman prompt, and the OpenRouter
script are in **[references/council.md](references/council.md)**. Read it before running this mode.

> Note on subscriptions: a ChatGPT Plus or Gemini Advanced **UI subscription does not grant API
> access** — a script can't drive them. Programmatic council needs API keys (OpenRouter for
> one-key simplicity, or direct OpenAI/Gemini keys; Gemini's API has a free tier). See
> [references/providers.md](references/providers.md).

## Mode C — Grounded (NotebookLM)

Best when answers must stay **anchored to a specific set of sources** — a spec, a bundle of
papers, internal docs — with citations and near-zero hallucination. NotebookLM ingests the
corpus and answers only from it.

Access is via a community NotebookLM bridge (MCP or CLI) plus Google auth. Setup, the available
bridges, and the ingest→query→extract flow are in
**[references/notebooklm.md](references/notebooklm.md)**. If no bridge is configured, fall back
to web-sweep over the same sources and say grounded mode was unavailable.

## Output — the research brief

Unless the caller asks for another shape, return this:

```markdown
# Research brief: <question>

## Bottom line
<2–4 sentences: the answer / recommendation, stated plainly.>

## Key findings
- <finding> — <why it matters> [source]
- ...

## Comparison / options   (when the question is "which X")
| Option | Strengths | Weaknesses | Best when |
|--------|-----------|------------|-----------|

## Risks & unknowns
- <what could bite us, what's unverified, where sources disagreed>

## Recommendation
<the call, tied to this session's goal and constraints — not generic advice>

## Sources
- [title](url) — <one line on what it supported>
```

Rules for the brief:

- **Tie it to the session.** A recommendation that ignores the established constraints is a
  failure, however well-researched. Reference the actual goal and context.
- **Cite load-bearing claims.** Every claim that moves the recommendation gets a source or an
  explicit "inference / unverified" label.
- **Separate fact from inference.** Don't launder a guess as a finding.
- **Surface disagreement.** If sources or council members conflict, say so — that's signal, not
  noise to be averaged away.
- **Be honest about coverage.** If you capped the search, skipped a mode, or couldn't verify
  something, state it. Silent truncation reads as "fully covered" when it isn't.

## When you're called from another skill

Return the brief as **structured data the caller can act on**, not a user-facing essay, unless
the caller says otherwise. Keep it tight and decision-oriented — the caller will weave it into
its own flow. See [references/embedding.md](references/embedding.md) for the skill-creator hook
and how to pass goal/context in.

## Reference files

- [references/council.md](references/council.md) — multi-model council: procedure, prompts, OpenRouter script
- [references/notebooklm.md](references/notebooklm.md) — grounded mode: bridges, setup, ingest/query flow
- [references/providers.md](references/providers.md) — API keys, OpenRouter vs direct, the subscription-vs-API reality
- [references/embedding.md](references/embedding.md) — calling research from skill-creator and other skills
- `scripts/council.py` — optional OpenRouter-backed council runner (read references/council.md first)
