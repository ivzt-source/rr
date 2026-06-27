# Council mode — multi-model deliberation

Based on Andrej Karpathy's [LLM Council](https://github.com/karpathy/llm-council). The premise:
asking several models the same question and letting them **review each other blind** catches
mistakes that any single model — however good — would confidently make alone. It mirrors the
manual workflow of asking ChatGPT, Gemini, and Claude the same thing and reconciling the
answers, but automates the reconcile step and removes brand bias.

## The three stages

1. **Independent answers.** Give the same question + session context to N members. Each answers
   on its own, with no view of the others. Diversity is the whole point — see "diversity" below.
2. **Anonymized peer review.** Give each member the *other* members' answers with **identities
   stripped** (label them "Response A/B/C…"). Each member critiques and ranks them. Anonymizing
   is the key trick from the original: it stops a model from flattering its own family or
   deferring to a big-name vendor.
3. **Chairman synthesis.** One designated model receives all answers + all reviews and writes
   the single final answer — resolving conflicts explicitly rather than averaging them.

## Choosing the engine

### Default: Claude subagents (no keys, runs here)

Use this unless you specifically need different *vendors*. Spawn N subagents as council members,
each with a **deliberately different framing** so they don't converge:

- Member 1 — **risk-first**: "What goes wrong with each option? What's the failure mode?"
- Member 2 — **simplest-thing-that-works**: "What's the least complex path to the goal?"
- Member 3 — **user/outcome-first**: "What best serves the end user / the stated goal?"
- (add a **prior-art** member: "What do mature projects in this space actually do?")

Then:

1. Run all members in the same turn (parallel), each answering independently from the same
   goal+context. Collect their answers.
2. Anonymize: relabel answers as "Response A/B/C". Spawn a review pass (one subagent per member,
   or one reviewer over all) that critiques and ranks the anonymized set.
3. Chairman pass: a final subagent (or you) reads answers + reviews and writes the synthesis,
   calling out where members disagreed and why the chosen position wins.

This approximates a multi-vendor council using prompt diversity instead of model diversity. It
won't catch a blind spot *common to all Claude models*, which is the one thing real multi-vendor
buys you.

### Optional: real multi-vendor via OpenRouter (one key)

When you want genuine cross-family diversity, use `scripts/council.py`, which calls multiple
models through a single [OpenRouter](https://openrouter.ai) key. One key, one bill, any mix of
GPT / Gemini / Claude / Llama / etc.

```bash
export OPENROUTER_API_KEY=sk-or-...
python scripts/council.py \
  --question "Should we use approach X or Y given <context>?" \
  --context-file /path/to/session-context.md \
  --members openai/gpt-5 google/gemini-2.5-pro anthropic/claude-opus-4-8 \
  --chairman anthropic/claude-opus-4-8 \
  --out council-result.md
```

The script implements all three stages (independent → anonymized review → chairman) and writes a
markdown report plus the raw per-stage JSON. Read the script header for flags. Model IDs change —
check OpenRouter's model list rather than trusting hardcoded names.

See [providers.md](providers.md) for key setup and why a ChatGPT/Gemini **subscription** can't be
used here (UI subscriptions ≠ API access).

## Diversity is the whole value

A council of near-identical voices is just one voice with extra latency. Whichever engine you
use, force divergence:

- Different model families (multi-vendor), **or** different framings (subagents), ideally both.
- Different priors: risk-averse vs. ship-fast, generalist vs. domain-specialist.
- Keep the review **blind** — never tell a member which answer was whose.

## Output

Fold the council result back into the standard research brief (see SKILL.md). In the brief's
**Risks & unknowns** section, surface where members *disagreed* — divergence is signal about
where the question is genuinely hard, not noise to smooth over.

## Cost & latency note

A council is N answers + N reviews + 1 synthesis ≈ 2N+1 model calls. Worth it for high-stakes or
contested decisions; overkill for a simple fact lookup (use web-sweep there). State in the brief
that a council was run and with which members — it's part of how much to trust the conclusion.
