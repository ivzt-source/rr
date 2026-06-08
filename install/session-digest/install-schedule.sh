#!/usr/bin/env bash
#
# install-schedule.sh — install the daily Claude session-digest job.
#
# It copies the digest scripts to a stable location, writes a config file
# pointing at YOUR private repo checkout, and schedules a daily run
# (launchd on macOS, cron on Linux).
#
# Usage:
#   ./install-schedule.sh --repo /path/to/your/private-repo-clone [options]
#
# Options:
#   --repo DIR        REQUIRED. Local git checkout of your private repo.
#   --time HH:MM      Daily run time, 24h local (default 07:00).
#   --days N          Days of history to include (default 7).
#   --subdir NAME     Subdir inside the repo (default claude-sessions).
#   --uninstall       Remove the schedule (keeps your repo + config).
#
# Prereq: create a PRIVATE GitHub repo, clone it locally, and pass its path
# to --repo. The job pushes the digest there each morning; read it on mobile
# via the GitHub app or github.com.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/claude-session-digest"
CONF="$HOME/.config/claude-session-digest.conf"
LABEL="com.claude.session-digest"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/.local/share/claude-session-digest/run.log"

REPO=""; TIME="07:00"; DAYS="7"; SUBDIR="claude-sessions"; ACTION="install"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --time) TIME="$2"; shift 2;;
    --days) DAYS="$2"; shift 2;;
    --subdir) SUBDIR="$2"; shift 2;;
    --uninstall) ACTION="uninstall"; shift;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

HOUR="${TIME%%:*}"; MIN="${TIME##*:}"
HOUR="$((10#$HOUR))"; MIN="$((10#$MIN))"
OS="$(uname -s)"

uninstall() {
  if [ "$OS" = "Darwin" ]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST" && echo "removed launchd job $PLIST"
  else
    if command -v crontab >/dev/null 2>&1; then
      ( crontab -l 2>/dev/null | grep -v "$APP_DIR/session-digest.sh" ) | crontab - || true
      echo "removed cron entry"
    fi
  fi
  echo "Schedule removed. (Config $CONF and your repo were left in place.)"
  exit 0
}
[ "$ACTION" = "uninstall" ] && uninstall

# ---- validate --------------------------------------------------------------
[ -n "$REPO" ] || { echo "ERROR: --repo is required." >&2; exit 1; }
REPO="$(cd "$REPO" 2>/dev/null && pwd)" || { echo "ERROR: --repo path not found." >&2; exit 1; }
[ -d "$REPO/.git" ] || { echo "ERROR: $REPO is not a git checkout." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required." >&2; exit 1; }

# ---- install files ---------------------------------------------------------
mkdir -p "$APP_DIR" "$(dirname "$CONF")"
cp "$SRC_DIR/render_digest.py" "$SRC_DIR/session-digest.sh" "$APP_DIR/"
chmod +x "$APP_DIR/session-digest.sh"
echo "✓ installed scripts -> $APP_DIR"

cat > "$CONF" <<EOF
# Claude session-digest config (generated $(date '+%Y-%m-%d %H:%M'))
DIGEST_REPO_DIR=$REPO
DIGEST_DAYS=$DAYS
DIGEST_SUBDIR=$SUBDIR
EOF
echo "✓ wrote config -> $CONF"

# ---- schedule --------------------------------------------------------------
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
    <string>$APP_DIR/session-digest.sh</string>
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
  echo "✓ scheduled via launchd daily at $(printf '%02d:%02d' "$HOUR" "$MIN") -> $PLIST"
else
  command -v crontab >/dev/null 2>&1 || { echo "ERROR: crontab not found." >&2; exit 1; }
  LINE="$MIN $HOUR * * * /bin/bash $APP_DIR/session-digest.sh >> $LOG 2>&1"
  ( crontab -l 2>/dev/null | grep -v "$APP_DIR/session-digest.sh"; echo "$LINE" ) | crontab -
  echo "✓ scheduled via cron daily at $(printf '%02d:%02d' "$HOUR" "$MIN")"
fi

echo
echo "Done. Test it now with a one-off run:"
echo "    bash $APP_DIR/session-digest.sh"
echo "Then open your private repo's '$SUBDIR/README.md' on your phone."
