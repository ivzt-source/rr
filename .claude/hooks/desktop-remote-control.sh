#!/usr/bin/env bash
# SessionStart hook: on local (desktop) sessions, instruct Claude to run the
# `remote-control` skill (equivalent to typing /remote-control) before doing
# anything else.
#
# Surface detection caveat: Claude Code does NOT expose a documented signal that
# separates the desktop app from the terminal CLI. It DOES set
# CLAUDE_CODE_REMOTE=true for remote/web sessions. So we treat "not remote" as
# "local/desktop" and skip remote/web (and anything else that sets that flag).
set -euo pipefail

# Skip remote/web sessions — only auto-run on local (desktop/CLI) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  exit 0
fi

# Inject an instruction Claude sees at the very start of the session.
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Local/desktop session detected. Before responding to the user, invoke the `remote-control` skill (the same thing as running the /remote-control command) using the Skill tool. Run it exactly once at the start of this session, then continue with whatever the user asked."
  }
}
JSON
