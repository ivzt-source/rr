#!/usr/bin/env bash
#
# install-remote-control.sh
# -------------------------
# Installs the `remote-control` skill GLOBALLY (user level) so it is available
# in EVERY Claude Code project/session on this machine — not just one repo.
#
# What it does:
#   1. Writes the skill to    ~/.claude/skills/remote-control/SKILL.md
#   2. Writes the hook to      ~/.claude/hooks/desktop-remote-control.sh
#   3. Merges a SessionStart hook into ~/.claude/settings.json (startup+resume)
#      WITHOUT clobbering any settings/hooks you already have.
#
# It is idempotent: run it as many times as you like. Re-running refreshes the
# files and de-dupes the hook entry.
#
# Usage:
#   bash install-remote-control.sh            # install / update
#   bash install-remote-control.sh --uninstall
#
# Respects $CLAUDE_CONFIG_DIR if you've set it; otherwise uses ~/.claude.
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_DIR/skills/remote-control"
HOOKS_DIR="$CLAUDE_DIR/hooks"
HOOK_PATH="$HOOKS_DIR/desktop-remote-control.sh"
SETTINGS="$CLAUDE_DIR/settings.json"

info() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

# ---- pick a JSON engine (python3 preferred, jq fallback) --------------------
JSON_ENGINE=""
if command -v python3 >/dev/null 2>&1; then JSON_ENGINE="python3"
elif command -v jq      >/dev/null 2>&1; then JSON_ENGINE="jq"
fi

# ---------------------------------------------------------------------------
uninstall() {
  echo "Uninstalling remote-control skill from $CLAUDE_DIR ..."
  rm -rf "$SKILL_DIR" && info "removed $SKILL_DIR"
  rm -f  "$HOOK_PATH" && info "removed $HOOK_PATH"
  if [ -f "$SETTINGS" ] && [ "$JSON_ENGINE" = "python3" ]; then
    HOOK_PATH="$HOOK_PATH" python3 - "$SETTINGS" <<'PY'
import json, os, sys
p = sys.argv[1]; hp = os.environ["HOOK_PATH"]
try:
    d = json.load(open(p))
except Exception:
    sys.exit(0)
ss = d.get("hooks", {}).get("SessionStart")
if isinstance(ss, list):
    kept = []
    for entry in ss:
        entry["hooks"] = [h for h in entry.get("hooks", [])
                          if hp not in (h.get("command") or "")]
        if entry["hooks"]:
            kept.append(entry)
    if kept:
        d["hooks"]["SessionStart"] = kept
    else:
        d["hooks"].pop("SessionStart", None)
        if not d["hooks"]:
            d.pop("hooks", None)
    json.dump(d, open(p, "w"), indent=2); open(p, "a").write("\n")
PY
    info "removed hook entries from $SETTINGS"
  elif [ -f "$SETTINGS" ] && [ "$JSON_ENGINE" = "jq" ]; then
    # jq installs the hook (see below), so jq must be able to remove it too —
    # otherwise uninstall deletes the hook script but leaves a dangling
    # SessionStart entry that errors on every session start.
    tmp="$(mktemp)"
    if jq --arg hook "$HOOK_PATH" '
        .hooks //= {}
        | .hooks.SessionStart = (
            (.hooks.SessionStart // [])
            | map(.hooks = ((.hooks // []) | map(select(.command != $hook)))
                  | select((.hooks | length) > 0)))
        | if (.hooks.SessionStart | length) == 0 then .hooks |= del(.SessionStart) else . end
        | if (.hooks | length) == 0 then del(.hooks) else . end
      ' "$SETTINGS" > "$tmp"; then
      mv "$tmp" "$SETTINGS"
      info "removed hook entries from $SETTINGS (jq)"
    else
      rm -f "$tmp"
      warn "could not process $SETTINGS with jq — remove the SessionStart entry by hand if needed"
    fi
  else
    warn "leave $SETTINGS untouched (remove the SessionStart entry by hand if needed)"
  fi
  echo "Done."
  exit 0
}

[ "${1:-}" = "--uninstall" ] && uninstall

# ---------------------------------------------------------------------------
echo "Installing remote-control skill into $CLAUDE_DIR ..."
mkdir -p "$SKILL_DIR" "$HOOKS_DIR"

# ---- 1. SKILL.md -----------------------------------------------------------
cat > "$SKILL_DIR/SKILL.md" <<'SKILL_EOF'
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
  session, via the `SessionStart` hook in `~/.claude/settings.json`
  (`~/.claude/hooks/desktop-remote-control.sh`).
- **Manually** any time you type `/remote-control`.

> Note on "desktop only": Claude Code does not expose a signal that
> distinguishes the desktop app from the terminal CLI. The hook detects
> **remote/web** sessions (`CLAUDE_CODE_REMOTE=true`) and skips them, so this
> runs on all *local* sessions (desktop **and** terminal CLI). See
> `~/.claude/hooks/desktop-remote-control.sh` for details.

## Procedure

1. TODO: Describe the first thing remote-control should do.
2. TODO: ...
3. TODO: ...

## Notes

- Keep this skill idempotent — it runs at the start of every local session, so
  it must be safe to run repeatedly.
- If you want it to also run on `/clear` or after compaction, add those
  matchers in `~/.claude/settings.json`.
SKILL_EOF
info "skill  -> $SKILL_DIR/SKILL.md"

# ---- 2. hook ---------------------------------------------------------------
cat > "$HOOK_PATH" <<'HOOK_EOF'
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
HOOK_EOF
chmod +x "$HOOK_PATH"
info "hook   -> $HOOK_PATH"

# ---- 3. merge settings.json ------------------------------------------------
if [ -z "$JSON_ENGINE" ]; then
  warn "neither python3 nor jq found — cannot safely merge $SETTINGS."
  warn "Add this SessionStart hook to $SETTINGS by hand:"
  cat <<MANUAL

  "hooks": {
    "SessionStart": [
      { "matcher": "startup", "hooks": [ { "type": "command", "command": "$HOOK_PATH" } ] },
      { "matcher": "resume",  "hooks": [ { "type": "command", "command": "$HOOK_PATH" } ] }
    ]
  }
MANUAL
  exit 1
fi

if [ "$JSON_ENGINE" = "python3" ]; then
  HOOK_PATH="$HOOK_PATH" SETTINGS="$SETTINGS" python3 - <<'PY'
import json, os
settings = os.environ["SETTINGS"]; hook = os.environ["HOOK_PATH"]
try:
    with open(settings) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError
except FileNotFoundError:
    data = {}
except Exception:
    bak = settings + ".bak"
    os.replace(settings, bak)
    print(f"  ! existing {settings} was not valid JSON; backed up to {bak}")
    data = {}

hooks = data.setdefault("hooks", {})
ss = hooks.get("SessionStart")
if not isinstance(ss, list):
    ss = []

# Drop any prior entries that point at our hook (idempotent re-install).
cleaned = []
for entry in ss:
    if not isinstance(entry, dict):
        cleaned.append(entry); continue
    entry["hooks"] = [h for h in entry.get("hooks", [])
                      if hook not in (h.get("command") or "")]
    # keep the matcher entry only if it still has hooks OR wasn't ours at all
    if entry["hooks"]:
        cleaned.append(entry)

for matcher in ("startup", "resume"):
    cleaned.append({
        "matcher": matcher,
        "hooks": [{"type": "command", "command": hook}],
    })

hooks["SessionStart"] = cleaned
data["hooks"] = hooks
with open(settings, "w") as f:
    json.dump(data, f, indent=2); f.write("\n")
print(f"  \033[32m✓\033[0m settings -> merged SessionStart hook into {settings}")
PY
else
  # jq fallback
  tmp="$(mktemp)"
  # Mirror the python3 path: if the existing file isn't valid JSON, back it up
  # and start fresh rather than failing outright.
  if [ -f "$SETTINGS" ] && ! jq empty "$SETTINGS" >/dev/null 2>&1; then
    mv "$SETTINGS" "$SETTINGS.bak"
    warn "existing $SETTINGS was not valid JSON; backed up to $SETTINGS.bak"
  fi
  [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
  # Check jq's exit status explicitly: `jq ... > "$tmp" && mv` would let a jq
  # failure fall through to the success message (errexit does not fire on the
  # left of &&), leaving the hook unregistered while claiming success.
  if jq --arg hook "$HOOK_PATH" '
    .hooks //= {} |
    .hooks.SessionStart = (
      ((.hooks.SessionStart // [])
        | map(.hooks = ((.hooks // []) | map(select(.command != $hook)))
              | select((.hooks | length) > 0)))
      + [ {matcher:"startup", hooks:[{type:"command", command:$hook}]},
          {matcher:"resume",  hooks:[{type:"command", command:$hook}]} ]
    )' "$SETTINGS" > "$tmp"; then
    mv "$tmp" "$SETTINGS"
    info "settings -> merged SessionStart hook into $SETTINGS (jq)"
  else
    rm -f "$tmp"
    warn "could not merge SessionStart hook into $SETTINGS with jq — hook NOT registered."
    warn "fix or remove $SETTINGS and re-run, or add the hook by hand (see above)."
    exit 1
  fi
fi

echo
echo "Done. The remote-control skill is now installed globally."
echo "Start a new local Claude Code session, or run /remote-control any time."
