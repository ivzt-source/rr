#!/usr/bin/env bash
#
# install-tasks.sh — install the `tasks` task-manager: the CLI, the Claude
# skill, and (optionally) a daily agenda job that publishes to a private repo.
#
# Usage:
#   ./install-tasks.sh                      # CLI + skill only
#   ./install-tasks.sh --repo /path/to/private-repo [--time 07:00]
#                                           # also schedule the daily agenda
#   ./install-tasks.sh --uninstall          # remove CLI, skill, schedule
#
# Options:
#   --repo DIR     Local git checkout of your private repo. Enables the daily
#                  agenda job that pushes agenda/README.md there each morning.
#   --time HH:MM   Daily agenda run time, 24h local (default 07:00).
#   --subdir NAME  Subdir inside the repo (default agenda).
#   --uninstall    Remove everything this installer added.
#
# Respects $CLAUDE_CONFIG_DIR (default ~/.claude). Idempotent; safe to re-run.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/claude-tasks"
CONF="$HOME/.config/claude-tasks.conf"
LABEL="com.claude.tasks-agenda"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$APP_DIR/run.log"

REPO=""; TIME="07:00"; SUBDIR="agenda"; ACTION="install"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --time) TIME="$2"; shift 2;;
    --subdir) SUBDIR="$2"; shift 2;;
    --uninstall) ACTION="uninstall"; shift;;
    -h|--help) sed -n '2,20p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

OS="$(uname -s)"

uninstall() {
  rm -f "$BIN_DIR/tasks" && echo "removed $BIN_DIR/tasks" || true
  rm -rf "$CFG_DIR/skills/tasks" && echo "removed skill $CFG_DIR/skills/tasks" || true
  rm -rf "$APP_DIR" || true
  if [ "$OS" = "Darwin" ]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST" && echo "removed launchd job $PLIST" || true
  elif command -v crontab >/dev/null 2>&1; then
    ( crontab -l 2>/dev/null | grep -v "$APP_DIR/tasks-agenda.sh" ) | crontab - || true
    echo "removed cron entry (if any)"
  fi
  echo "Uninstalled. (Config $CONF and your task store were left in place.)"
  exit 0
}
[ "$ACTION" = "uninstall" ] && uninstall

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required." >&2; exit 1; }

# ---- 1. install the CLI ----------------------------------------------------
mkdir -p "$BIN_DIR" "$APP_DIR"
cp "$SRC_DIR/tasks.py" "$APP_DIR/tasks.py"
cp "$SRC_DIR/tasks-agenda.sh" "$APP_DIR/tasks-agenda.sh"
chmod +x "$APP_DIR/tasks-agenda.sh"
cat > "$BIN_DIR/tasks" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/tasks.py" "\$@"
EOF
chmod +x "$BIN_DIR/tasks"
echo "✓ installed CLI -> $BIN_DIR/tasks"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "  note: $BIN_DIR is not on your PATH — add it to use \`tasks\` directly.";;
esac

# ---- 2. install the Claude skill -------------------------------------------
mkdir -p "$CFG_DIR/skills/tasks"
cp "$SRC_DIR/../../.claude/skills/tasks/SKILL.md" "$CFG_DIR/skills/tasks/SKILL.md"
echo "✓ installed skill -> $CFG_DIR/skills/tasks/SKILL.md"

# ---- 3. optional daily agenda schedule -------------------------------------
if [ -z "$REPO" ]; then
  echo
  echo "Done (CLI + skill). To also publish a daily agenda to your phone, re-run with:"
  echo "    ./install-tasks.sh --repo /path/to/your/private-repo-clone"
  exit 0
fi

REPO="$(cd "$REPO" 2>/dev/null && pwd)" || { echo "ERROR: --repo path not found." >&2; exit 1; }
[ -d "$REPO/.git" ] || { echo "ERROR: $REPO is not a git checkout." >&2; exit 1; }

mkdir -p "$(dirname "$CONF")"
cat > "$CONF" <<EOF
# Claude tasks agenda config (generated $(date '+%Y-%m-%d %H:%M'))
AGENDA_REPO_DIR=$REPO
AGENDA_SUBDIR=$SUBDIR
# TASKS_DIR=$HOME/.tasks
EOF
echo "✓ wrote config -> $CONF"

HOUR="$((10#${TIME%%:*}))"; MIN="$((10#${TIME##*:}))"
if [ "$OS" = "Darwin" ]; then
  mkdir -p "$(dirname "$PLIST")"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$APP_DIR/tasks-agenda.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MIN</integer></dict>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "✓ scheduled via launchd daily at $(printf '%02d:%02d' "$HOUR" "$MIN")"
else
  command -v crontab >/dev/null 2>&1 || { echo "ERROR: crontab not found." >&2; exit 1; }
  LINE="$MIN $HOUR * * * /bin/bash $APP_DIR/tasks-agenda.sh >> $LOG 2>&1"
  ( crontab -l 2>/dev/null | grep -v "$APP_DIR/tasks-agenda.sh"; echo "$LINE" ) | crontab -
  echo "✓ scheduled via cron daily at $(printf '%02d:%02d' "$HOUR" "$MIN")"
fi

echo
echo "Done. Test the agenda job now with a one-off run:"
echo "    bash $APP_DIR/tasks-agenda.sh"
echo "Then open '$SUBDIR/README.md' in your private repo on your phone."
