#!/usr/bin/env bash
#
# verify.sh — the project's acceptance gate ("the bar").
#
# Runs every automated check and exits 0 only if ALL of them pass. This is the
# single source of truth for "is the work done?" — used both by CI
# (.github/workflows/ci.yml) and by the goal-driven loop (see LOOP.md).
#
# It runs every check even if an earlier one fails, so each iteration shows the
# full picture rather than stopping at the first problem.
#
# Usage:
#   scripts/verify.sh
#
# Exit code: 0 = bar met (all checks pass), 1 = bar not met.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

fail=0
section() { printf '\n=== %s ===\n' "$1"; }

# ---- 1. Python tests -------------------------------------------------------
section "pytest"
if command -v pytest >/dev/null 2>&1; then
  pytest || fail=1
elif python3 -c 'import pytest' >/dev/null 2>&1; then
  python3 -m pytest || fail=1
else
  echo "ERROR: pytest not installed (pip install -r requirements-dev.txt)" >&2
  fail=1
fi

# ---- 2. ShellCheck ---------------------------------------------------------
section "shellcheck"
if command -v shellcheck >/dev/null 2>&1; then
  if find . -name '*.sh' -not -path './.git/*' -print0 \
       | xargs -0 -r shellcheck --severity=warning; then
    echo "shellcheck: clean"
  else
    fail=1
  fi
else
  echo "ERROR: shellcheck not installed" >&2
  fail=1
fi

# ---- verdict ---------------------------------------------------------------
section "result"
if [ "$fail" -eq 0 ]; then
  echo "PASS — the bar is met."
else
  echo "FAIL — the bar is not met yet." >&2
fi
exit "$fail"
