#!/usr/bin/env bash
#
# tasks-agenda.sh — render today's task agenda to Markdown and publish it to a
# (private) git repo so you can read it on your phone each morning.
#
# Sibling of session-digest.sh: same config-file + retry/backoff conventions.
#
# Reads config from, in order of precedence:
#   1. environment variables
#   2. ~/.config/claude-tasks.conf   (KEY=VALUE lines)
#
# Required:
#   AGENDA_REPO_DIR   local path to a git checkout of your private repo
# Optional:
#   TASKS_DIR         where tasks.txt lives (default ~/.tasks)
#   AGENDA_SUBDIR     subdir inside the repo to write into (default: agenda)
#   AGENDA_BRANCH     branch to push (default: current branch of the repo)
#
# Exit codes: 0 ok (incl. "nothing changed"), non-zero on real failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$SCRIPT_DIR/tasks.py"
CONF="${CLAUDE_TASKS_CONF:-$HOME/.config/claude-tasks.conf}"

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"; }
die() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# ---- load config file (does not override already-set env) -------------------
if [ -f "$CONF" ]; then
  while IFS='=' read -r k v; do
    case "$k" in ''|\#*) continue;; esac
    k="$(echo "$k" | tr -d '[:space:]')"
    v="${v#"${v%%[![:space:]]*}"}"   # ltrim
    [ -z "${!k:-}" ] && export "$k=$v" || true
  done < "$CONF"
fi

AGENDA_SUBDIR="${AGENDA_SUBDIR:-agenda}"
export TASKS_DIR="${TASKS_DIR:-$HOME/.tasks}"

[ -n "${AGENDA_REPO_DIR:-}" ] || die "AGENDA_REPO_DIR is not set (env or $CONF)."
[ -d "$AGENDA_REPO_DIR/.git" ] || die "$AGENDA_REPO_DIR is not a git checkout."
[ -f "$CLI" ] || die "tasks CLI not found at $CLI"
command -v python3 >/dev/null 2>&1 || die "python3 is required."

cd "$AGENDA_REPO_DIR"
BRANCH="${AGENDA_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

# ---- refresh local checkout (best effort) ----------------------------------
log "pulling latest on $BRANCH ..."
git pull --ff-only origin "$BRANCH" >/dev/null 2>&1 || log "  (pull skipped/failed — continuing)"

# ---- render ----------------------------------------------------------------
OUT="$AGENDA_REPO_DIR/$AGENDA_SUBDIR"
mkdir -p "$OUT"
log "rendering agenda from $TASKS_DIR ..."
python3 "$CLI" agenda --out "$OUT/README.md"
# also keep a dated snapshot for history
DATED="$OUT/$(date '+%Y-%m-%d').md"
cp "$OUT/README.md" "$DATED"

# ---- commit & push ---------------------------------------------------------
git add "$AGENDA_SUBDIR"
if git diff --cached --quiet; then
  log "no changes since last run — nothing to publish."
  exit 0
fi

git commit -q -m "Task agenda: $(date '+%Y-%m-%d %H:%M')"
log "pushing to origin/$BRANCH ..."
n=0
until git push origin "$BRANCH" >/dev/null 2>&1; do
  n=$((n+1)); [ "$n" -ge 4 ] && die "git push failed after retries."
  sleep $((2 ** n)); log "  push retry $n ..."
done
log "published $AGENDA_SUBDIR to origin/$BRANCH."
