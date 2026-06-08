#!/usr/bin/env bash
#
# session-digest.sh — render the last N days of local Claude Code sessions to
# Markdown and publish them to a (private) git repo so you can read them on
# mobile (e.g. via the GitHub app/website).
#
# Reads config from, in order of precedence:
#   1. environment variables
#   2. ~/.config/claude-session-digest.conf   (KEY=VALUE lines)
#
# Required:
#   DIGEST_REPO_DIR   local path to a git checkout of your private repo
# Optional:
#   DIGEST_DAYS       default 7
#   DIGEST_SUBDIR     subdir inside the repo to write into (default: claude-sessions)
#   DIGEST_BRANCH     branch to push (default: current branch of the repo)
#   CLAUDE_CONFIG_DIR default ~/.claude
#
# Exit codes: 0 ok (incl. "nothing changed"), non-zero on real failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDERER="$SCRIPT_DIR/render_digest.py"
CONF="${CLAUDE_DIGEST_CONF:-$HOME/.config/claude-session-digest.conf}"

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

DIGEST_DAYS="${DIGEST_DAYS:-7}"
DIGEST_SUBDIR="${DIGEST_SUBDIR:-claude-sessions}"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

[ -n "${DIGEST_REPO_DIR:-}" ] || die "DIGEST_REPO_DIR is not set (env or $CONF)."
[ -d "$DIGEST_REPO_DIR/.git" ] || die "$DIGEST_REPO_DIR is not a git checkout."
[ -f "$RENDERER" ] || die "renderer not found at $RENDERER"
command -v python3 >/dev/null 2>&1 || die "python3 is required."

cd "$DIGEST_REPO_DIR"
BRANCH="${DIGEST_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

# ---- refresh local checkout (best effort) ----------------------------------
log "pulling latest on $BRANCH ..."
git pull --ff-only origin "$BRANCH" >/dev/null 2>&1 || log "  (pull skipped/failed — continuing)"

# ---- render ----------------------------------------------------------------
OUT="$DIGEST_REPO_DIR/$DIGEST_SUBDIR"
mkdir -p "$OUT"
log "rendering last $DIGEST_DAYS day(s) from $CLAUDE_CONFIG_DIR ..."
CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" python3 "$RENDERER" \
  --claude-dir "$CLAUDE_CONFIG_DIR" --days "$DIGEST_DAYS" --out "$OUT"

# ---- commit & push ---------------------------------------------------------
git add "$DIGEST_SUBDIR"
if git diff --cached --quiet; then
  log "no changes since last run — nothing to publish."
  exit 0
fi

git commit -q -m "Session digest: last $DIGEST_DAYS days ($(date '+%Y-%m-%d %H:%M'))"
log "pushing to origin/$BRANCH ..."
n=0
until git push origin "$BRANCH" >/dev/null 2>&1; do
  n=$((n+1)); [ "$n" -ge 4 ] && die "git push failed after retries."
  sleep $((2 ** n)); log "  push retry $n ..."
done
log "published $DIGEST_SUBDIR to origin/$BRANCH."
