#!/usr/bin/env bash
#
# loop.sh — run the acceptance gate (scripts/verify.sh) repeatedly until it
# passes, or until a maximum number of attempts is reached.
#
# This is the *mechanical* loop: it re-runs the bar but cannot change code on
# its own, so it only makes progress if something (you, in another window, or
# an agent) is editing files between attempts. For the *agentic* loop — where
# Claude reads each failure and fixes the code until the bar passes — see
# LOOP.md.
#
# Usage:
#   scripts/loop.sh [--max N] [--sleep SECONDS]
#
# Exit code: 0 = bar met within N attempts, 1 = still failing after N attempts.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX=10
SLEEP=5

while [ $# -gt 0 ]; do
  case "$1" in
    --max) MAX="$2"; shift 2;;
    --sleep) SLEEP="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

attempt=1
while :; do
  printf '\n##### attempt %d/%d #####\n' "$attempt" "$MAX"
  if "$REPO_ROOT/scripts/verify.sh"; then
    echo "Bar met on attempt $attempt."
    exit 0
  fi
  if [ "$attempt" -ge "$MAX" ]; then
    echo "Bar still not met after $MAX attempts." >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep "$SLEEP"
done
