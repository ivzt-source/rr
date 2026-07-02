# CLAUDE.md

## What this repo is

`rr` is a personal toolkit of Claude Code skills, hooks, installers, and
scheduled jobs, plus business/marketing working documents. Most artifacts here
exist to bridge three platform gaps: no native scheduling, cloud sessions
can't reach the desktop `~/.claude`, and local sessions aren't readable on
mobile. Check whether an existing artifact already solves (or half-solves)
your problem before building a new one — see `install/` and `.claude/skills/`.

## Branch and landing policy

- Pull requests target `main`. Never base a PR on another `claude/*` session
  branch.
- A session that produces durable work is not finished at `git push`. Open a
  PR, get CI green, and merge (or explicitly hand the merge decision back to
  the user). Do not leave green PRs open or push branches with no PR.
- Before starting new work, check for open PRs and unmerged `claude/*`
  branches touching the same area; build on merged `main`, not on a sibling
  session branch.

## The bar (definition of done)

- Run `scripts/verify.sh` before pushing. It is the single acceptance gate,
  identical to CI: pytest + shellcheck.
- New shell scripts must pass shellcheck; new Python gets tests in `tests/`.
- If you write a backlog ("not yet covered", "pending", TODO), also open a
  GitHub issue for it — untracked backlogs in READMEs never get picked up.

## Installers, scheduling, and boilerplate

- Anything that must land in the user's real `~/.claude`, crontab, or launchd
  cannot be done from a cloud session — ship an installer script the user runs
  on the desktop, and say so plainly in the session summary.
- Do not hand-roll a new installer, config loader, launchd/cron scheduler, or
  git-push retry loop. Extend the shared library (`install/lib.sh`; if it
  does not exist yet, factor it out of `install/install-remote-control.sh`,
  `install/session-digest/`, and `install/tasks/` rather than adding a fourth
  copy). Installers copy from the checkout (no embedded heredoc copies of
  skills — they drift).
- Recurring jobs that only need GitHub (not local files) should be cloud-side
  (scheduled cloud session or GitHub Action), not desktop cron.

## Works-today rule

A skill's primary path must be exercised end-to-end before it ships. If a
backend needs credentials, an unreleased upstream, or an unvetted bridge that
this session cannot exercise, ship only the fallback as the primary path and
label the rest experimental, with its missing prerequisite listed in
`context/secrets-setup.md`.

## Business context (for marketing/sales/copy sessions)

- Business: Safety Nest — life insurance for Australian SMSF trustees
  (core angle: rolling super into an SMSF cancels the old fund's group
  life/TPD cover). Sender identity for outbound: **TBC — fill in name the
  SMS/email sends as**. Company legal/trading name for copy: **TBC**.
- Before writing any outbound copy, read `context/business.md`,
  `context/brand-voice.md`, and `context/compliance-au.md` (create them from
  the best existing branch content if missing — do not restate the business
  from scratch in the deliverable).
- Voice: friendly, low-pressure, casual Australian register; never "book a
  call" pressure framing — always offer a choice of channel.
- Hard rules for outbound: cold SMS/email always carries opt-out language
  (Spam Act); every factual/statistical claim in ad copy links to the research
  fact base or is marked `[BLOCKING: unverified]`; financial-product copy is
  written to ASIC RG 234 (no unsubstantiated case studies — label illustrative
  scenarios as such).

## Prose style

Spell out technical abbreviations on first use in authored prose (skills,
READMEs, docs): "command-line interface (CLI)", then the abbreviation
thereafter. Applies to documentation prose, not code identifiers.
