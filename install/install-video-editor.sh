#!/usr/bin/env bash
#
# install-video-editor.sh
# -----------------------
# Installs the `video-editor` skill GLOBALLY (user level) so it is available in
# EVERY Claude Code project/session on this machine — not just the `rr` repo.
#
# The skill drives video edits from Claude Code via OpenCut (the open-source
# CapCut alternative) when its MCP server is running, and falls back to ffmpeg
# otherwise. It is a plain skill — no hooks, no settings.json changes — so this
# installer just copies the skill into ~/.claude/skills/.
#
# It is idempotent: run it as many times as you like.
#
# Usage:
#   bash install-video-editor.sh            # install / update
#   bash install-video-editor.sh --uninstall
#
# Respects $CLAUDE_CONFIG_DIR if you've set it; otherwise uses ~/.claude.
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_DIR/skills/video-editor"

# Source skill (this script lives in install/, the skill in ../.claude/skills/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_SKILL="$SCRIPT_DIR/../.claude/skills/video-editor/SKILL.md"

info() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

uninstall() {
  echo "Uninstalling video-editor skill from $CLAUDE_DIR ..."
  rm -rf "$SKILL_DIR" && info "removed $SKILL_DIR"
  echo "Done."
  exit 0
}

[ "${1:-}" = "--uninstall" ] && uninstall

echo "Installing video-editor skill into $CLAUDE_DIR ..."

if [ ! -f "$SRC_SKILL" ]; then
  warn "could not find skill source at $SRC_SKILL"
  warn "run this script from a checkout of the repo (install/install-video-editor.sh)."
  exit 1
fi

mkdir -p "$SKILL_DIR"
cp "$SRC_SKILL" "$SKILL_DIR/SKILL.md"
info "skill -> $SKILL_DIR/SKILL.md"

echo
echo "Done. The video-editor skill is now installed globally."
echo "Run /video-editor any time, or just ask Claude to trim/caption/render a clip."
echo
echo "For full timeline editing, also set up OpenCut's headless MCP server —"
echo "see the 'OpenCut MCP server' section in the skill for the commands."
