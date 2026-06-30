---
name: tasks
description: Personal + business task management. Capture, triage, and review tasks from natural language and from Gmail / Google Calendar / Slack. Use whenever the user wants to add a todo, plan their day/week, ask "what's on", do a weekly review, or turn an email/message/meeting into an action. Backed by the `tasks` CLI (a plain-text, git-friendly store).
---

# Tasks — business + personal

A natural-language front-end over the `tasks` CLI. The CLI is the source of
truth (plain text in `$TASKS_DIR`, default `~/.tasks`); your job is to translate
what the user says into precise CLI calls, and to pull actionable items out of
their email, calendar, and Slack.

## The CLI

Run `tasks <cmd>`. If `tasks` isn't on PATH, use
`python3 ~/.local/share/claude-tasks/tasks.py` (or the repo copy at
`install/tasks/tasks.py`).

| Want to… | Command |
|---|---|
| Add | `tasks add "Call accountant" -a business -p A -d tomorrow -P BizTax -c phone` |
| List (open) | `tasks list` · filters: `-a business` `-P Proj` `-c phone` `-p A` `--overdue` `--due-before friday` `-s text` |
| Today's agenda | `tasks today` |
| Complete | `tasks done <id> [<id>...]` |
| Re/de-prioritize | `tasks pri <id> A` (or `-` to clear) |
| Edit | `tasks edit <id> [new text] -d 2026-07-05 -a personal -P Proj -c context` |
| Delete | `tasks rm <id>` |
| Archive completed | `tasks archive` |
| Overviews | `tasks areas` · `tasks projects` |
| Markdown agenda (mobile) | `tasks agenda [-o path]` |

**Fields.** `-a/--area` is `business` or `personal` (the life split — always set
it). `-p/--priority` is `A`–`Z` (A = must-do). `-d/--due` accepts
`YYYY-MM-DD`, `today`, `tomorrow`, `+Nd`, or a weekday name. `-P/--project`
groups related work (`+BizTax`); `-c/--context` is where/how (`@phone`,
`@errand`, `@waiting`, `@desk`). IDs are the short `[abc]` tokens in listings.

## How to behave

**Capturing.** When the user mentions something to do, add it immediately — don't
interrogate. Infer `area` from content (work/clients/invoices → business; home/
family/health → personal). Set a `due` only if they imply one. Confirm tersely
with the resulting line. Batch multiple todos into multiple `add` calls.

**"What's on?" / planning the day.** Run `tasks today`. Lead with overdue, then
due-today, then priority-A. Offer to re-date or re-prioritize anything stale.
Keep it short and scannable.

**Triage from other tools** (only when asked, or during a review):
- **Gmail** — search action-required mail (e.g. starred/important or
  `is:starred`, `label:follow-up`). For each genuine action, create a task with
  a `+project` for the thread and `area:business`/`personal`; note the sender in
  the description. Don't turn newsletters/receipts into tasks.
- **Calendar** — pull the next 1–7 days of events. Surface prep tasks
  ("prep for 2pm client call") and deadlines. Don't duplicate the meeting itself
  as a task unless prep/followup is needed.
- **Slack** — scan messages addressed to the user / threads they're in for
  commitments ("I'll send…", "can you…"). Capture the real asks as tasks with a
  `@waiting` context if they're blocked on someone else.

Always show the user what you captured and from where; never silently invent
tasks. If a source is ambiguous, ask before adding more than a couple.

**Weekly review** (when asked for a review, or "plan my week"):
1. `tasks list --all` and `tasks archive` to clear completed.
2. Pull from Gmail / Calendar / Slack as above.
3. Walk `tasks areas` and `tasks projects`; flag stale items (old `created`, no
   `due`), suggest priorities for the week, and propose 3–5 `A` tasks per area.
4. End with a crisp summary of the week's focus.

## Conventions & guardrails

- **Always set `area`.** The business/personal split is the point.
- Prefer a few well-chosen `A` tasks over many. If everything is `A`, nothing is.
- Reference tasks by their `[id]`; show the formatted line after any change.
- The store is plain text and git-friendly — never hand-edit it when a CLI
  command exists. Run `tasks archive` periodically so listings stay short.
- A scheduled job (`tasks-agenda.sh`) can publish a Markdown agenda to a private
  repo each morning for mobile — see `install/tasks/README.md`.

> This skill tailors easily to a specific methodology (GTD, PARA, time-blocking,
> etc.). If the user names one, adopt its vocabulary for projects/contexts and
> its review cadence — the CLI fields already support it.
