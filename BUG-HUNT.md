# Bug hunt — 2026-07-02

Scope: all three recent commits (`ab70a44`, `37e7216`, `7653af0`) — the remote-control
skill/hook/installer and the session-digest pipeline. Method: 6 parallel reviewers with
distinct lenses (shell correctness, Python logic, installer state, cross-file consistency,
security/privacy, runtime edge cases) produced 18 raw findings; deduplicated to 12; each
verified by an adversarial 3-lens panel (refute / reproduce / impact). All 12 were
confirmed 3–0; several were reproduced by actually executing the failing code path.

## Ranked findings

### 1. HIGH — Cron install self-destructs under `set -e`/`pipefail`
`install/session-digest/install-schedule.sh:111`

```sh
( crontab -l 2>/dev/null | grep -v "$APP_DIR/session-digest.sh"; echo "$LINE" ) | crontab -
```

The subshell inherits `set -euo pipefail`. When `crontab -l` fails (no crontab yet — the
default on a fresh Linux box) or `grep -v` filters every line (re-install when the digest
entry is the only crontab line), the inner pipeline returns non-zero, errexit aborts the
subshell **before** `echo "$LINE"`, and `crontab -` receives empty input:

- **First install**: installs an empty crontab, exits 1, job never scheduled — a partial
  install (scripts + config written, no schedule).
- **Re-install** (e.g. changing `--time`): **wipes the existing working schedule** and exits 1.

Reproduced empirically. The uninstall path (line 53) only survives because of its trailing
`|| true`.

**Fix:** add the same guard on the read side:
`( crontab -l 2>/dev/null | grep -v "$APP_DIR/session-digest.sh" || true; echo "$LINE" ) | crontab -`

### 2. HIGH — Digest filename collision silently overwrites the real session
`install/session-digest/render_digest.py:157` (root cause shared with #7, line 123)

Filenames are `{day}-{sid[:8]}.md` with no collision handling. Subagent transcripts
(`projects/<proj>/<session>/subagents/**/*.jsonl`) carry the **same** `sessionId` as their
parent session, so the parent and every subagent it spawned that day map to the identical
filename and each write clobbers the last. Reproduced against a real `~/.claude` tree:
3 "sessions" rendered, 1 file produced, index links all pointing at it, and the surviving
content was a subagent transcript — the actual user session was silently lost. Any session
that uses subagents (very common) loses its digest.

**Fix:** fix #7 (exclude subagent transcripts from discovery) *and* add a collision guard —
track used filenames and append `-2`, `-3`, … before writing.

### 3. MEDIUM — jq merge path reports success when jq fails; hook never registered
`install/install-remote-control.sh:227`

`jq ... "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"` — a failing left side of `&&` is
exempt from errexit, so with a pre-existing invalid `settings.json` the script prints the
"✓ settings -> merged" banner and exits 0 while the file was never touched. The hook
silently never activates, and the mktemp file leaks. The python3 path handles the same
input correctly (backs up to `.bak` and rebuilds), so behavior diverges based on which
tool happens to be installed. Verified live.

**Fix:** `if ! jq ... > "$tmp"; then rm -f "$tmp"; warn ...; exit 1; fi; mv "$tmp" "$SETTINGS"` —
or mirror the python3 path's backup-and-rebuild behavior.

### 4. MEDIUM — Uninstall leaves a dangling SessionStart hook on jq-only systems
`install/install-remote-control.sh:44`

Install merges the hook via python3 **or** jq, but `uninstall()` only strips the
settings entry when python3 is present. On a jq-only machine, uninstall deletes the hook
script and skill but leaves both `startup`/`resume` entries pointing at the now-missing
file — every subsequent session start fires a broken hook until settings.json is
hand-edited. Contradicts `install/README.md` ("strips only its own entry").

**Fix:** add a jq branch to `uninstall()` running the inverse of the install filter
(drop hooks whose `command` matches, prune empty entries/keys).

### 5. MEDIUM — Daily job crashes when the digest repo has no commits yet
`install/session-digest/session-digest.sh:49`

`BRANCH="${DIGEST_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"` exits 128 on an unborn
HEAD. The documented setup ("create a private GitHub repo and clone it") produces exactly
that state when the repo is created without a README. `install-schedule.sh` only checks
`.git` exists, so this passes install validation and then the scheduled job fails every
run with a cryptic error in a log nobody reads.

**Fix:** `BRANCH="${DIGEST_BRANCH:-$(git symbolic-ref --short -q HEAD || echo main)}"` —
`symbolic-ref` resolves the unborn branch name.

### 6. MEDIUM — Config parser fatally aborts on non-identifier keys
`install/session-digest/session-digest.sh:35`

The comment filter runs **before** whitespace is stripped from `$k`, so an indented
comment (`  # note`) in the user-editable conf file reaches `[ -z "${!k:-}" ]`. Indirect
expansion with an invalid name is a fatal expansion error that `|| true` does **not**
catch (reproduced: script exits 1 before rendering). The daily job dies at config-load.

**Fix:** trim `$k` before the `case` filter and skip non-identifier keys:
`case "$k" in ''|\#*|[0-9]*|*[!A-Za-z0-9_]*) continue;; esac`.

### 7. MEDIUM — Subagent/sidechain transcripts rendered as user sessions
`install/session-digest/render_digest.py:123`

`glob(projects/**/*.jsonl, recursive=True)` matches subagent files under
`<session>/subagents/**`, and `load_session` never checks `isSidechain`. Confirmed with
real data: one user session rendered as three "sessions", two of them internal subagent
transcripts titled with orchestrator-injected prompts. Inflates counts and (via #2)
destroys real digests.

**Fix:** glob only one level (`projects/*/*.jsonl`) or skip records with
`o.get("isSidechain")` in `load_session`.

### 8. MEDIUM/LOW — Unescaped titles break Markdown index links
`install/session-digest/render_digest.py:186`

Titles are raw first prompts; any `]` in the prompt (e.g. `fix arr[i]`) breaks the
CommonMark link, and 80-char truncation can cut pasted Markdown mid-link. `html` is
imported (line 17) but never used — the intended escaping was never wired up. Same raw
interpolation into the `# {title}` heading at line 160.

**Fix:** escape `\`, `[`, `]` in link text; strip leading `#` for the heading.

### 9. LOW — Slash-command / isMeta messages become the session title
`install/session-digest/render_digest.py:88`

Only `<local-command-stdout>` is filtered. `<command-name>…` slash-command records and
`isMeta` lines (the "Caveat: …" message) leak into turns, and when first become the
session title/index text instead of the user's real prompt.

**Fix:** skip records where `o.get("isMeta")` and texts starting with `<command-name>`.

### 10. LOW — Truncation can cut inside a code fence
`install/session-digest/render_digest.py:117`

A 6000-char slice that lands inside a ``` fence drops the closing fence; every later
turn in that session file renders inside an unterminated code block.

**Fix:** if `s[:n].count("```")` is odd, append `\n```` before the truncation marker.

### 11. LOW — `--time` without a colon silently schedules HH:HH
`install/session-digest/install-schedule.sh:43`

`--time 8` → HOUR=8, MIN=8 → runs at 08:08; `--time 24:00` produces an invalid entry that
only fails at crontab/launchctl time.

**Fix:** validate `^([01]?[0-9]|2[0-3]):[0-5][0-9]$` before splitting.

### 12. LOW — "No-op if nothing changed" is unreachable
`install/session-digest/README.md:63` vs `render_digest.py:148`

The index embeds a minute-resolution "Generated …" timestamp, so `git diff --cached
--quiet` sees a change on every run — a commit is pushed daily even with zero session
activity. The documented no-op path is dead code.

**Fix:** drop the generated-at timestamp (or derive it from the newest session's
`ts_last`), or exclude that line from the change check.

## Suggested fix order

1. **#1** (one-line `|| true`) — unbreaks Linux install and stops schedule destruction.
2. **#7 + #2 together** in `render_digest.py` — one discovery change plus a collision
   counter; restores digest integrity.
3. **#5, #6** in `session-digest.sh` — two small guards; makes the daily job robust.
4. **#3, #4** in `install-remote-control.sh` — error-check the jq merge, add the jq
   uninstall branch.
5. **#8–#12** — rendering polish and validation, batched in one pass.
