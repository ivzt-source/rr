# Goal-driven loop, wired to this repo's CI

The "loop" pattern is simple: define a **measurable** bar, then let an agent
work — checking against the bar and fixing failures — until it passes, instead
of producing one answer and stopping. The human sets the goal once; the agent
does the check-fix-recheck cycle.

This repo now has the two pieces that make that real.

## 1. The bar — `scripts/verify.sh`

A single, objective gate. It exits `0` only when **both**:

- every `pytest` test passes, and
- `shellcheck` is clean (warning severity) across every `*.sh`.

```bash
scripts/verify.sh        # prints each check, then PASS or FAIL; exits accordingly
```

CI (`.github/workflows/ci.yml`) runs the **exact same script**, so "green
locally" and "green on the PR" mean the same thing — there's one definition of
done, not two.

## 2. The loop

### Mechanical — `scripts/loop.sh`
Re-runs the bar until it passes or hits `--max`. It cannot fix code itself, so
it only helps when something is editing files between attempts (handy as a
watch window while you work):

```bash
scripts/loop.sh --max 10 --sleep 5
```

### Agentic — Claude fixes until green (the real thing)
Give Claude the goal *and* the bar, and let it iterate hands-off:

> Run `scripts/verify.sh`. If it fails, read the output, fix the cause, then run
> it again. Repeat until it passes. Don't stop until the bar is green.

Two ways to drive it without babysitting:

- **`/loop` skill** — e.g. `/loop 5m run scripts/verify.sh and fix anything that
  fails`, which re-enters the task on an interval until you stop it.
- **PR subscription** — subscribe the PR so a CI failure wakes a fixing loop
  automatically, and the agent keeps pushing fixes until the checks are green.

## Why the bar must be measurable

The goal has to be something the agent can **check by itself** — exit codes,
test counts, lint findings. "Make it look good" can't close a loop because
nothing can grade it automatically; "`pytest` + `shellcheck` exit 0" can. That
objectivity is the whole trick: it's what lets the agent decide, without you,
whether it's done.
