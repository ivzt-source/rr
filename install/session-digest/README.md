# Daily session digest → read your last 7 days on mobile

A scheduled job that runs **on your desktop**, renders the last N days of your
local Claude Code session transcripts to Markdown, and pushes them to a
**private GitHub repo**. You then read them on your phone via the GitHub mobile
app or github.com.

> ⚠️ Important honesty note: this does **not** put sessions inside the Claude
> mobile app — that isn't possible (the app's list is server-side cloud
> sessions only). This is the working alternative: your recent local sessions,
> readable on your phone, in a repo you control.

## What gets published

```
<your-private-repo>/claude-sessions/
  README.md                     index, grouped by day, newest first
  sessions/<date>-<id>.md       one readable transcript per session
```

Each transcript shows your prompts and Claude's replies; tool calls are
collapsed to one-liners (`🔧 used tool: Bash`) and internal "thinking" is
omitted, so it reads cleanly on a phone.

## One-time setup (on your desktop)

1. **Create a PRIVATE GitHub repo** (e.g. `claude-journal`) and clone it:
   ```bash
   git clone git@github.com:<you>/claude-journal.git ~/claude-journal
   ```
2. **Install the daily schedule**, pointing at that clone:
   ```bash
   bash install/session-digest/install-schedule.sh --repo ~/claude-journal --time 07:00
   ```
   This copies the scripts to `~/.local/share/claude-session-digest/`, writes
   config to `~/.config/claude-session-digest.conf`, and schedules a daily run
   (launchd on macOS, cron on Linux).
3. **Test it immediately:**
   ```bash
   bash ~/.local/share/claude-session-digest/session-digest.sh
   ```
   Then open `claude-sessions/README.md` in your repo on your phone.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--repo DIR` | (required) | Local checkout of your private repo |
| `--time HH:MM` | `07:00` | Daily run time (local, 24h) |
| `--days N` | `7` | Days of history to include |
| `--subdir NAME` | `claude-sessions` | Folder inside the repo |

Config precedence: environment variables override
`~/.config/claude-session-digest.conf`. Respects `$CLAUDE_CONFIG_DIR`
(defaults to `~/.claude`).

## Run manually any time

```bash
bash ~/.local/share/claude-session-digest/session-digest.sh
```

It's a no-op if nothing changed since the last run, and retries the push with
backoff on network errors.

## Uninstall the schedule

```bash
bash install/session-digest/install-schedule.sh --uninstall
```

Removes the launchd/cron entry. Your private repo and config file are left
untouched.

## Caveats

- **Runs where the sessions live.** Local transcripts are on the machine that
  ran them, so install this on each desktop you want covered. It can't pull
  sessions from other machines.
- **Privacy:** transcripts can contain code, paths, and secrets you pasted.
  Keep the target repo **private**.
- **The job needs push access** — make sure `git push` works non-interactively
  from the repo clone (SSH key or cached credential helper); a daily cron/launchd
  run can't answer a password prompt.
- Laptop must be awake at the scheduled time (cron/launchd don't wake it). On
  macOS, launchd will run a missed job shortly after wake.
