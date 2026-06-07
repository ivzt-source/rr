---
name: remote-control
description: Remote-control workflow for desktop Claude Code sessions. Auto-invoked at the start of every local/desktop session via a SessionStart hook, and runnable manually with /remote-control. SCAFFOLD — replace the steps below with the real behavior.
---

# Remote Control

> ⚠️ **SCAFFOLD** — this skill is a placeholder. The auto-run wiring is fully
> working; replace the steps in the **Procedure** section with the actual
> remote-control behavior you want.

## When this runs

- **Automatically** at the start of every **local/desktop** Claude Code
  session, via the `SessionStart` hook in `.claude/settings.json`
  (`.claude/hooks/desktop-remote-control.sh`).
- **Manually** any time you type `/remote-control`.

> Note on "desktop only": Claude Code does not expose a signal that
> distinguishes the desktop app from the terminal CLI. The hook detects
> **remote/web** sessions (`CLAUDE_CODE_REMOTE=true`) and skips them, so this
> runs on all *local* sessions (desktop **and** terminal CLI). See
> `.claude/hooks/desktop-remote-control.sh` for details.

## Procedure

1. TODO: Describe the first thing remote-control should do.
2. TODO: ...
3. TODO: ...

## Notes

- Keep this skill idempotent — it runs at the start of every local session, so
  it must be safe to run repeatedly.
- If you want it to also run on `/clear` or after compaction, add those
  matchers in `.claude/settings.json`.
