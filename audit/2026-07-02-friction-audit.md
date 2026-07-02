# Friction audit of recent Claude Code sessions (Jun 7 – Jul 2, 2026)

**Method.** This audit ran in a cloud session, so your desktop transcripts
(`~/.claude/projects/` on your machine) were not reachable — ironically the
exact gap your session-digest job exists to close. Instead, four parallel
sub-agents mined the durable artifacts of your last 8 sessions: every remote
branch of this repo, all commits, both pull requests and their discussion, and
the GitHub Actions history. That's enough to see where you keep hitting the
same walls; a richer pass over full transcripts is possible once the digest
repo is readable from a session (see Automation A3).

**Sessions audited** (one branch each, newest first):

| Date | Branch | What it was |
|------|--------|-------------|
| Jul 2 | `smsf-marketing-campaign-research` | Safety Nest SMSF campaign skeleton (ICP, funnel, copy bank) |
| Jun 30 | `sms-cold-lead-opener` | Cold-lead SMS opener rewrite |
| Jun 30 | `task-management-system` | todo.txt-style tasks CLI + skill + daily agenda cron |
| Jun 30 | `video-editor-agent-setup` | OpenCut MCP video-editor skill + ffmpeg fallback |
| Jun 27 | `skill-builder-skills` | Research skill (web / council / NotebookLM) + vendored skill-creator (PR #2) |
| Jun 9–27 | `test-coverage-analysis` | pytest suite, CI, `verify.sh` acceptance gate, LOOP.md (PR #1) |
| Jun 7–8 | `remote-control-desktop-skill` | Remote-control SessionStart hook (scaffold) + session-digest cron |

---

## Friction clusters, ranked by cost

### 1. Nothing ever lands — the repo has no `main`

The default branch is itself a session branch
(`claude/remote-control-desktop-skill-ng7xS`). Every session forks from it,
pushes, and stops:

- PR #1 (tests + CI): open since **Jun 9**, CI green all 4 runs, zero reviews, never merged.
- PR #2 (research skill): open since Jun 27, never merged — and got **zero CI runs**, because the CI workflow lives only on PR #1's unmerged branch.
- 4 more branches (sms, smsf, tasks, video-editor) never even got a PR.
- The tasks branch (Jun 30) shipped `tasks.py` + `tasks-agenda.sh` **without ever passing "the bar"** you built on Jun 27, because the branches never met.
- The follow-up backlog you wrote down in `tests/README.md` ("not yet covered: install-remote-control merge, session-digest retry, hook gating") was never picked up by any later session.

**Cost:** every improvement (CI, verify.sh, style fixes) applies to exactly one
branch and evaporates; sessions keep rebuilding on stale scaffolding.
**Fix:** cluster-1 items in the Skills/Automations/CLAUDE.md sections below —
create `main`, land the branches, and make "merge when green" the default
end-state of a session instead of "push and abandon."

### 2. The same three platform gaps get re-solved by hand every time

Every infrastructure artifact in this repo is a workaround for the same trio:

- **No scheduling** → hand-rolled launchd/cron installers, twice (`install-schedule.sh`, `install-tasks.sh`), each with the same fragility caveats ("laptop must be awake", "cron can't answer a password prompt").
- **Cloud sessions can't reach your real `~/.claude`** → three separate "run this on your desktop, not in a cloud session" installers (`install-remote-control.sh`, `install-schedule.sh`, `install-video-editor.sh`). The video-editor commit message literally says "mirroring install-remote-control.sh" — the pattern is being re-derived per artifact.
- **No mobile surface for local state** → push-Markdown-to-private-GitHub-repo, built twice (session digest, tasks agenda), with the config-loader, `git pull --ff-only`, and exponential-backoff push retry copied nearly verbatim between `session-digest.sh` and `tasks-agenda.sh`.

**Cost:** each new capability pays a ~200-line boilerplate tax and drifts
independently (bugfixes to one copy never reach the others — the SC2097 export
fix landed only on the test branch).
**Fix:** one shared `install/lib.sh` + an `installer` skill (S2), and shift
recurring jobs to cloud-native scheduling where possible (A3).

### 3. Business sessions start from zero context, every time

There is **no CLAUDE.md and no business context file anywhere in the repo**.
Consequences visible in the artifacts:

- The SMS opener ships with `[Name]`, `[Your Name]`, `[Company]` — the session never knew who you are or what the business is called. It also re-invents tone rules ("never 'book a call' framing") that clearly existed before, and references an "SMS qualifying sequence" and "standard follow-up cadence" that exist nowhere Claude can see.
- The SMSF campaign defines the brand ("Safety Nest"), offer, ICP, and methodology from scratch, carries **~13 `[RESEARCH: …]` placeholders**, and gates every piece of copy on two files (`04-research-fact-base.md`, `05-compliance-guardrails.md`) that were **never created**.
- Compliance is inconsistent because it lives in no shared doc: the SMSF session flags ASIC RG 234 / SIS Reg 4.09 on nearly every claim, while the SMS opener has **no opt-out/consent language at all** — a real Spam Act exposure for cold SMS in Australia.

**Cost:** every marketing session re-derives (or worse, skips) brand, offer,
voice, and compliance; outputs aren't launchable without manual work the
session couldn't know about.
**Fix:** CLAUDE.md business section + `context/` docs (C4), a `copywriting`
skill that loads them (S3), and one deep-research session to finally produce
the fact base both campaigns are blocked on (A4).

### 4. Speculative integrations ship as the "primary path"

A consistent tell across skills: the headline backend was never exercised, and
the skill ships with a pre-written apology:

- **OpenCut MCP**: commands are "the shape", tool names "discover at runtime", status text pre-plans its own failure ("tell the user the MCP path needs OpenCut's rewrite build"). Only the ffmpeg fallback works today.
- **Research council**: the real multi-vendor path needs an OpenRouter key that was never configured; `council.py` is "compile-checked but not run against a live service."
- **NotebookLM grounded mode**: depends on an unvetted community browser-automation bridge; no `.mcp.json` was ever committed.
- **Remote-control**: the flagship — installed globally, auto-runs at the start of **every local session** via the SessionStart hook, and its Procedure is still `1. TODO / 2. TODO / 3. TODO` since Jun 7. Every desktop session begins by dutifully invoking a skill that does nothing.

**Cost:** setup effort spent on paths that don't run; the remote-control
scaffold actively wastes the first turn of every local session.
**Fix:** fill or disable remote-control now (A1), a "works today first" rule in
CLAUDE.md (C5), and a `secrets-setup` checklist so keyed integrations either
get their keys or get cut (S4).

### 5. Style preferences re-litigated across sessions

Two entire commits (`053b3ca`, `66523ef`) plus a PR-body note ("per reviewer
preference…") exist only to spell out abbreviations after the fact. That's a
one-line CLAUDE.md rule being paid for repeatedly in review churn.

### 6. Follow-through has no owner

Self-created backlogs (`tests/README.md` "not yet covered", the SMSF "pending
fact base", the remote-control TODOs) are written down and never revisited; no
GitHub issues exist; PRs get no reviews. The repo accumulates honest,
well-documented unfinished work with no mechanism that ever surfaces it again.
**Fix:** the weekly gardener automation (A2) exists precisely to be that
mechanism.

---

## Proposed new skills

**S1. `/land` — finish-line skill.** Ends the "push and abandon" pattern.
Procedure: ensure branch is rebased on `main` → run `scripts/verify.sh` → open
PR to `main` (not to a session branch) → subscribe to PR activity → fix until
green → enable auto-merge → confirm merge → delete branch. Invoke at the end
of any session that produced durable work. (Directly addresses cluster 1;
pairs with automation A2.)

**S2. `installer` — global-install scaffolder.** Captures the pattern you've
now hand-built three times. Contents: a shared `install/lib.sh` (config-file
loader, idempotent `~/.claude` copy respecting `$CLAUDE_CONFIG_DIR`, safe
settings.json merge with the python3/jq/manual fallback, launchd/cron
schedule + `--uninstall`, exponential-backoff git push). The skill's job:
"given a new skill/hook/job, generate its installer from lib.sh" — never
re-derive the boilerplate, never fork it. Also documents the one real
gotcha you've hit both ways: heredoc-embedded copies drift, copy-from-checkout
requires a checkout; lib.sh should standardize on copy-from-checkout with a
version stamp. (Cluster 2.)

**S3. `copywriting` — brand-context loader for marketing/sales sessions.**
Front-matter triggers on SMS/email/ad/campaign work. Procedure: read
`context/business.md`, `context/brand-voice.md`,
`context/compliance-au.md` before writing a word of copy; refuse to emit
cold-SMS copy without opt-out language; use real business/sender names instead
of `[Company]`; link every claim to the fact base or mark it blocking. (Cluster 3.)

**S4. `secrets-setup` — credential preflight.** One doc + checklist skill
listing every integration you've adopted and the key it needs (OpenRouter for
the council, NotebookLM bridge choice, OpenCut endpoint), with a "configured?
tested?" status. Sessions building on these check the status first, and either
use the working path or explicitly descope — no more shipping compile-checked
integrations. (Cluster 4.)

**S5. Decide `remote-control`'s real job — or delete it.** It auto-runs at
every local session start, so it's the most valuable slot in your setup and
it's spending that slot on TODOs. Given what you've built since, the obvious
fill: *pull the journal/tasks repo and surface today's agenda + any stale
`claude/*` branches at session start* — you already wrote `tasks-agenda.sh`;
the skill just reads its output. If you don't want that, uninstall the hook.

## Proposed automations

**A1. (Immediate, one-off) Repo surgery.** Create `main` from the current
default branch, set it as GitHub default, merge PR #1 (green for 3 weeks),
rebase + merge PR #2 so it finally gets CI, then open PRs for the four
orphaned branches. After this, CI and `verify.sh` protect everything, not one
branch. I can do all of it from a session on request.

**A2. Weekly gardener (scheduled cloud session or GitHub Action).** Lists open
PRs and `claude/*` branches with no PR, checks CI, re-surfaces the written-down
backlogs (`tests/README.md`, SMSF pending items, TODO scaffolds), and posts a
short digest — into the journal repo you already read on your phone. This is
the missing follow-through mechanism (cluster 6). A cloud scheduled session
can do this without your laptop being awake — unlike your cron jobs.

**A3. Move recurring jobs cloud-side where they don't need local state.** The
session-digest *must* run on the desktop (transcripts are local), but the
gardener and any future recurring job that only touches GitHub should be
cloud-scheduled sessions — no launchd, no "laptop must be awake", no SSH-key
caveats. Bonus: once the digest repo exists, grant future cloud sessions read
access to it and "audit my sessions" gets full transcripts instead of artifact
archaeology.

**A4. One deep-research session to unblock the SMSF campaign.** Both
marketing branches are gated on `04-research-fact-base.md` and
`05-compliance-guardrails.md`. Run the deep-research skill once with the ~13
`[RESEARCH]` questions as the brief; commit both files into `context/` so the
SMS work inherits the compliance guardrails too.

## CLAUDE.md fixes

The repo had **no CLAUDE.md at all** — that absence is upstream of clusters 1,
3, and 5. A concrete proposed `CLAUDE.md` is committed alongside this report
(repo root). Summary of what it encodes and why:

- **C1 — Branch & landing policy:** PRs target `main`; a session that produces durable work ends with `/land`, not a bare push. (Cluster 1)
- **C2 — The bar:** run `scripts/verify.sh` before pushing; new scripts get tests; new shell goes under shellcheck. (Cluster 1/2)
- **C3 — Reuse the installer lib:** never hand-roll `~/.claude` installers, cron scheduling, or push-retry loops; extend `install/lib.sh`. (Cluster 2)
- **C4 — Business context:** who the business is, pointer to `context/` docs, and the hard rule that outbound copy carries opt-out language and no unsubstantiated claims. (Cluster 3)
- **C5 — Works-today rule:** a skill's primary path must be exercised end-to-end before shipping; speculative backends are explicitly labeled experimental and tracked in `secrets-setup`. (Cluster 4)
- **C6 — Style:** spell out technical abbreviations in prose — written once, so no more abbreviation-churn commits. (Cluster 5)

## Suggested order

1. **A1 repo surgery** (30 min, unblocks everything else — CI starts protecting all work).
2. **Merge CLAUDE.md** + fill in the two `TBC` business fields it flags.
3. **S5 remote-control decision** (it costs you the first turn of every local session today).
4. **S2 installer lib** next time an install-shaped task appears (don't do it speculatively).
5. **A4 deep-research fact base** before any more campaign copy.
6. **A2 weekly gardener** once `main` exists.
