# Calling research from another skill

The research skill is built to be **composable** — invoked on its own, or called as a step by
another skill once that skill has established a goal. This file documents the contract.

## The contract

A calling skill should pass research two things:

1. **Goal** — what the caller is trying to achieve (one or two sentences).
2. **Context** — the constraints already known: environment, stack, audience, budget, deadline,
   prior decisions. Pull these from the live session; don't make the user repeat them.

Research returns a **structured brief** (see the brief format in SKILL.md), oriented to a
decision rather than written as a user-facing essay. The caller decides how much of it to surface
to the user.

When invoked this way, run the **smallest mode that answers the question**:

- Background facts / prior art / "what do mature tools do" → **web sweep**.
- A genuine "which approach should we commit to" fork → **council**.
- Reasoning that must cite a fixed source set the caller already has → **grounded**.

Keep it tight. An embedded research call should inform the caller's next step, not derail into a
standalone report unless the caller asked for one.

## The skill-creator hook

`skill-creator` has an **"Interview and Research"** step that runs after intent is captured and
before SKILL.md is drafted. That step is the natural home for this skill. The vendored
skill-creator in this repo (`.claude/skills/skill-creator/`) invokes research there.

The reason this matters: the interview captures **what the user knows to tell you**. Research
captures **what they didn't know to mention** — that there's already an official skill for this,
that the obvious library has a known footgun, that two competing patterns exist and the choice
has consequences, what the real API surface looks like. Feeding that back *before* drafting
produces a far better first draft than interview-alone.

### What research surfaces for skill-creation specifically

- **Prior art** — does an official or popular skill/tool already do this? (Check
  `anthropics/skills`, the plugin marketplace, MCP servers.) Building on or differentiating from
  it beats reinventing it.
- **The real interface** — actual API/CLI/file formats the skill will touch, from primary docs,
  so the draft is concrete instead of hand-wavy.
- **Known gotchas** — footguns, rate limits, auth quirks, version traps worth encoding as
  instructions.
- **Competing approaches** — when there's more than one sane way, a quick council on "which
  pattern for this skill" prevents committing to the wrong one in the first draft.

### How the hook behaves

- Research runs **proactively but briefly** — a focused sweep, not an open-ended report. It
  should make the draft better, not stall the interview.
- Findings feed the **draft and its instructions**; cite primary sources for anything load-bearing
  (e.g. an API the skill depends on).
- It **degrades gracefully**: no web access → skill-creator proceeds on the interview alone and
  says research was skipped. The hook never blocks skill creation.
