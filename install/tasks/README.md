# `tasks` — business + personal task management

A small, self-hosted task system that fits this repo's pattern (plain-text +
git-friendly + scheduled mobile digests). Three parts:

1. **`tasks` CLI** (`tasks.py`) — a dependency-free task store. One task per
   line, todo.txt-style, readable and editable on your phone. The source of
   truth.
2. **`tasks` Claude skill** (`.claude/skills/tasks/SKILL.md`) — the
   natural-language front-end. Lets Claude capture todos, turn your Gmail /
   Calendar / Slack into tasks, run "what's on today", and do weekly reviews.
3. **Daily agenda job** (`tasks-agenda.sh`) — sibling of the session-digest
   job: renders today's agenda to a private repo each morning so you read it on
   your phone.

## Install

Run on the machine where you use Claude Code (your desktop), not in a cloud
session:

```bash
# CLI + skill only:
bash install/tasks/install-tasks.sh

# CLI + skill + daily agenda published to a private repo:
bash install/tasks/install-tasks.sh --repo /path/to/your/private-repo-clone --time 07:00
```

This:

1. installs the CLI to `~/.local/bin/tasks` (a thin wrapper over
   `~/.local/share/claude-tasks/tasks.py`),
2. installs the skill to `~/.claude/skills/tasks/` (available in every session),
3. with `--repo`, writes `~/.config/claude-tasks.conf` and schedules a daily
   `tasks-agenda.sh` run (launchd on macOS, cron on Linux).

Idempotent. Respects `$CLAUDE_CONFIG_DIR`. Uninstall with
`bash install/tasks/install-tasks.sh --uninstall`.

## Quick start

```bash
tasks add "Call accountant about BAS" -a business -p A -d tomorrow -P BizTax -c phone
tasks add "Book dentist" -a personal -d +10d
tasks today                 # overdue + due-today + priority-A, split by area
tasks list -a business      # filter by area / project / context / priority
tasks done <id>             # complete (ids are the [abc] tokens in listings)
tasks archive               # sweep completed into done.txt
```

Or just talk to Claude: *"add a task to call the accountant tomorrow",*
*"what's on today?",* *"turn my starred emails into tasks",* *"plan my week".*
The `tasks` skill handles the rest.

## Task format

```
(A) 2026-06-30 Call accountant about BAS +BizTax @phone area:business due:2026-07-05 id:k3f
```

- `(A)` priority `A`–`Z` · `2026-06-30` creation date (auto)
- `+Project` projects · `@context` where/how
- `area:` `business`|`personal` — the life split · `due:` optional deadline
- `id:` stable short id (auto). Completed lines start with `x <completion-date>`.

Store lives in `$TASKS_DIR` (default `~/.tasks`): `tasks.txt` (active) and
`done.txt` (archived). Both are plain text — back them up in a private git repo
and you can read/edit them anywhere.

## Daily agenda on mobile

With `--repo`, the scheduled job writes `agenda/README.md` (plus a dated
snapshot) to your private repo every morning and pushes it. Open it in the
GitHub mobile app to see overdue items, what's due today, top priorities, and
the next 7 days — same idea as the `session-digest` job.

## Notes

- The CLI is stdlib-only Python 3 — no dependencies.
- The skill can pull from Gmail / Calendar / Slack when those connectors are
  available in your session; it only ever adds tasks it shows you.
- Tailor the skill to a methodology (GTD, PARA, time-blocking) by telling Claude
  which one — the fields already support projects, contexts, priorities, and
  due dates.
