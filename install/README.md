# Install the `remote-control` skill globally

The skill lives in this repo's `.claude/` (project scope = the `rr` repo only).
This installer copies it to your **user-level** Claude Code config
(`~/.claude/`) so it's available in **every project/session** on your machine.

## One command (run on your desktop, not in a cloud session)

```bash
bash install/install-remote-control.sh
```

That:

1. writes the skill to `~/.claude/skills/remote-control/SKILL.md`
2. writes the hook to `~/.claude/hooks/desktop-remote-control.sh`
3. **merges** a `SessionStart` hook (startup + resume) into
   `~/.claude/settings.json` — it does **not** overwrite your existing settings
   or other hooks.

It's idempotent (safe to re-run) and de-dupes its own hook entry. Needs
`python3` or `jq` for the safe JSON merge; if neither is present it prints the
exact snippet to paste into `settings.json` yourself.

Respects `$CLAUDE_CONFIG_DIR` if you've set it; otherwise uses `~/.claude`.

## Verify

Start a new local Claude Code session — the hook injects an instruction to run
the skill automatically. Or run `/remote-control` any time.

## Uninstall

```bash
bash install/install-remote-control.sh --uninstall
```

Removes the skill + hook and strips only its own entry from
`~/.claude/settings.json`, leaving everything else intact.

## Notes / caveats

- **"Desktop only" isn't precisely detectable.** Claude Code exposes no signal
  separating the desktop app from the terminal CLI. The hook skips **remote/web**
  sessions (`CLAUDE_CODE_REMOTE=true`) and runs on all **local** sessions
  (desktop **and** terminal CLI) — the closest available approximation.
- The skill body is still a **scaffold** — the auto-run wiring works; replace
  the `Procedure` steps in `SKILL.md` with the real remote-control behavior.
- Must be run on the actual desktop machine. Running it inside an ephemeral
  Claude Code cloud/web container won't reach your real `~/.claude`.
