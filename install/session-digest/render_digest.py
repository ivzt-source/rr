#!/usr/bin/env python3
"""
render_digest.py — render recent Claude Code session transcripts to Markdown.

Reads local session transcripts from   <claude-dir>/projects/**/*.jsonl
keeps the ones touched in the last N days, and writes:

    <out>/README.md                 index, grouped by day, newest first
    <out>/sessions/<file>.md        one readable transcript per session

It is read-only with respect to your Claude data. Safe to run repeatedly;
it rewrites the output directory each run.

Usage:
    render_digest.py --claude-dir ~/.claude --days 7 --out ./out
"""
import argparse, json, os, glob, html
from datetime import datetime, timedelta, timezone

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--claude-dir", default=os.environ.get("CLAUDE_CONFIG_DIR",
                   os.path.expanduser("~/.claude")))
    p.add_argument("--days", type=int, default=int(os.environ.get("DIGEST_DAYS", "7")))
    p.add_argument("--out", required=True)
    p.add_argument("--max-chars", type=int, default=6000,
                   help="truncate any single message body to this many chars")
    return p.parse_args()

def text_from_content(content):
    """Extract human-readable text from a message.content (str or block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                out.append(b.get("text", ""))
            elif t == "tool_use":
                name = b.get("name", "tool")
                out.append(f"_🔧 used tool: `{name}`_")
            # thinking / tool_result are intentionally skipped here
        return "\n\n".join(s for s in out if s.strip())
    return ""

def is_tool_result_turn(obj):
    if obj.get("toolUseResult") is not None:
        return True
    c = obj.get("message", {}).get("content")
    if isinstance(c, list) and c and all(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
        return True
    return False

def load_session(path):
    """Return dict with meta + ordered list of (role, text) turns, or None if empty."""
    turns, first_user, cwd, branch, ts_first, ts_last, sid = [], None, None, None, None, None, None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("isSidechain"):
            continue  # subagent/sidechain line, not part of the user session
        typ = o.get("type")
        if typ not in ("user", "assistant"):
            continue
        ts = o.get("timestamp")
        if ts:
            ts_first = ts_first or ts
            ts_last = ts
        cwd = cwd or o.get("cwd")
        branch = branch or o.get("gitBranch")
        sid = sid or o.get("sessionId")
        msg = o.get("message", {}) or {}
        role = msg.get("role")
        if role == "user":
            if is_tool_result_turn(o):
                continue  # skip tool plumbing, keep it readable
            txt = text_from_content(msg.get("content"))
            if not txt.strip():
                continue
            # skip command stdout / reminder-only noise heuristically
            if txt.lstrip().startswith("<local-command-stdout>"):
                continue
            first_user = first_user or txt.strip()
            turns.append(("user", txt))
        elif role == "assistant":
            txt = text_from_content(msg.get("content"))
            if txt.strip():
                turns.append(("assistant", txt))
    if not turns:
        return None
    return dict(turns=turns, first_user=first_user or "(no prompt captured)",
                cwd=cwd, branch=branch, sid=sid,
                ts_first=ts_first, ts_last=ts_last, path=path)

def fmt_ts(ts):
    if not ts:
        return "?"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]

def day_of(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return "unknown-date"

def truncate(s, n):
    return s if len(s) <= n else s[:n] + f"\n\n…_[truncated {len(s)-n} chars]_"

def main():
    a = parse_args()
    proj_root = os.path.join(a.claude_dir, "projects")
    cutoff = datetime.now(timezone.utc) - timedelta(days=a.days)
    # Only top-level session transcripts (projects/<project>/<session>.jsonl).
    # Deeper files — e.g. projects/<project>/<session>/subagents/**/*.jsonl —
    # are subagent/sidechain transcripts that share the parent's sessionId; a
    # recursive glob would render them as separate sessions and collide on the
    # {day}-{sid[:8]} filename, silently overwriting the real session.
    files = glob.glob(os.path.join(proj_root, "*", "*.jsonl"))

    sessions = []
    for f in files:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc)
        except OSError:
            continue
        if mtime < cutoff:
            continue
        s = load_session(f)
        if s:
            s["mtime"] = mtime
            sessions.append(s)

    sessions.sort(key=lambda s: s.get("ts_last") or "", reverse=True)

    out_sessions = os.path.join(a.out, "sessions")
    os.makedirs(out_sessions, exist_ok=True)
    # clear stale generated files
    for old in glob.glob(os.path.join(out_sessions, "*.md")):
        os.remove(old)

    index = ["# Claude Code — last {} days of sessions".format(a.days),
             "",
             "_Generated {} UTC · {} session(s)_".format(
                 datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), len(sessions)),
             ""]

    by_day = {}
    used_names = set()
    for s in sessions:
        day = day_of(s.get("ts_last"))
        short = (s.get("sid") or os.path.basename(s["path"]))[:8]
        title = " ".join(s["first_user"].split())[:80]
        fname = "{}-{}.md".format(day, short)
        # Guard against filename collisions (two sessions sharing an 8-char id
        # prefix on the same day) so one digest never silently overwrites another.
        if fname in used_names:
            stem = "{}-{}".format(day, short)
            i = 2
            while "{}-{}.md".format(stem, i) in used_names:
                i += 1
            fname = "{}-{}.md".format(stem, i)
        used_names.add(fname)
        fpath = os.path.join(out_sessions, fname)

        body = ["# {}".format(title or "(untitled session)"), ""]
        body.append("- **Session:** `{}`".format(s.get("sid") or "?"))
        body.append("- **Project:** `{}`".format(s.get("cwd") or "?"))
        if s.get("branch"):
            body.append("- **Branch:** `{}`".format(s["branch"]))
        body.append("- **Span:** {} → {} UTC".format(fmt_ts(s["ts_first"]), fmt_ts(s["ts_last"])))
        body.append("- **Turns:** {}".format(len(s["turns"])))
        body.append("")
        body.append("---")
        body.append("")
        for role, txt in s["turns"]:
            label = "🧑 **You**" if role == "user" else "🤖 **Claude**"
            body.append("### {}".format(label))
            body.append("")
            body.append(truncate(txt.strip(), a.max_chars))
            body.append("")
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(body) + "\n")

        by_day.setdefault(day, []).append((title, fname, s, len(s["turns"])))

    for day in sorted(by_day, reverse=True):
        index.append("## {}".format(day))
        index.append("")
        for title, fname, s, nturns in by_day[day]:
            t = title or "(untitled)"
            index.append("- [{}](sessions/{}) — {} turns, `{}`".format(
                t, fname, nturns, fmt_ts(s["ts_last"])))
        index.append("")

    if not sessions:
        index.append("_No sessions in the last {} days._".format(a.days))

    with open(os.path.join(a.out, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(index) + "\n")

    print("rendered {} session(s) -> {}".format(len(sessions), a.out))

if __name__ == "__main__":
    main()
