#!/usr/bin/env python3
"""
tasks.py — a tiny, dependency-free task manager for business + personal life.

Design goals (matches this repo's other tools):
  * Plain-text, git-friendly store you can read/edit on your phone.
  * Deterministic CLI primitives so a human OR Claude can drive it reliably.
  * No third-party deps — Python 3 stdlib only.

Storage (todo.txt-inspired, one task per line) lives in $TASKS_DIR
(default ~/.tasks):
    tasks.txt   active tasks
    done.txt    completed tasks (moved here by `archive`)

A task line looks like:
    (A) 2026-06-30 Call accountant about BAS +BizTax @phone area:business due:2026-07-05 id:k3f

  (A)            optional priority A-Z (A = highest)
  2026-06-30     creation date (added automatically)
  +Project       zero or more projects
  @context       zero or more contexts (where/how: @phone, @errand, @waiting)
  area:business  business | personal  (the life split)
  due:YYYY-MM-DD optional due date
  id:k3f         stable short id (added automatically)

Completed lines are prefixed with `x ` and a completion date:
    x 2026-06-30 (A) 2026-06-29 Call accountant ... id:k3f

Run `tasks help` for commands.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import re
import string
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ----------------------------------------------------------------------------- config
AREAS = ("business", "personal")
PRIORITY_RE = re.compile(r"^\(([A-Z])\)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEYVAL_RE = re.compile(r"^([A-Za-z][\w-]*):(.+)$")
ID_ALPHABET = string.ascii_lowercase + string.digits


def store_dir() -> Path:
    return Path(os.environ.get("TASKS_DIR", str(Path.home() / ".tasks")))


def today() -> dt.date:
    return dt.date.today()


def iso(d: dt.date) -> str:
    return d.isoformat()


# ----------------------------------------------------------------------------- model
@dataclass
class Task:
    description: str = ""
    priority: str | None = None              # single uppercase letter
    created: dt.date | None = None
    completed: dt.date | None = None          # set => done
    projects: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    kv: dict[str, str] = field(default_factory=dict)  # includes id, area, due
    raw_index: int = -1                       # line position in source file

    # -- convenience views ----------------------------------------------------
    @property
    def done(self) -> bool:
        return self.completed is not None

    @property
    def id(self) -> str:
        return self.kv.get("id", "")

    @property
    def area(self) -> str:
        return self.kv.get("area", "")

    @property
    def due(self) -> dt.date | None:
        v = self.kv.get("due")
        if v and DATE_RE.match(v):
            try:
                return dt.date.fromisoformat(v)
            except ValueError:
                return None
        return None

    def overdue(self, ref: dt.date | None = None) -> bool:
        d = self.due
        return bool(d and not self.done and d < (ref or today()))

    # -- parse / serialize ----------------------------------------------------
    @classmethod
    def parse(cls, line: str) -> "Task | None":
        s = line.strip()
        if not s:
            return None
        t = cls()
        toks = s.split()
        i = 0
        if toks[i] == "x":
            i += 1
            if i < len(toks) and DATE_RE.match(toks[i]):
                t.completed = dt.date.fromisoformat(toks[i])
                i += 1
            else:
                t.completed = today()
        if i < len(toks):
            m = PRIORITY_RE.match(toks[i])
            if m:
                t.priority = m.group(1)
                i += 1
        if i < len(toks) and DATE_RE.match(toks[i]):
            t.created = dt.date.fromisoformat(toks[i])
            i += 1
        words: list[str] = []
        for tok in toks[i:]:
            if tok.startswith("+") and len(tok) > 1:
                t.projects.append(tok[1:])
            elif tok.startswith("@") and len(tok) > 1:
                t.contexts.append(tok[1:])
            else:
                km = KEYVAL_RE.match(tok)
                if km:
                    t.kv[km.group(1)] = km.group(2)
                else:
                    words.append(tok)
        t.description = " ".join(words)
        return t

    def serialize(self) -> str:
        parts: list[str] = []
        if self.done:
            parts.append("x")
            parts.append(iso(self.completed or today()))
        if self.priority:
            parts.append(f"({self.priority})")
        if self.created:
            parts.append(iso(self.created))
        if self.description:
            parts.append(self.description)
        for p in self.projects:
            parts.append(f"+{p}")
        for c in self.contexts:
            parts.append(f"@{c}")
        # stable, readable key order; remaining keys sorted
        ordered = ["area", "due"]
        for k in ordered:
            if k in self.kv:
                parts.append(f"{k}:{self.kv[k]}")
        for k in sorted(self.kv):
            if k in ordered or k == "id":
                continue
            parts.append(f"{k}:{self.kv[k]}")
        if "id" in self.kv:
            parts.append(f"id:{self.kv['id']}")
        return " ".join(parts)


# ----------------------------------------------------------------------------- store
class Store:
    def __init__(self) -> None:
        self.dir = store_dir()
        self.active_path = self.dir / "tasks.txt"
        self.done_path = self.dir / "done.txt"

    def _read(self, path: Path) -> list[Task]:
        if not path.exists():
            return []
        out: list[Task] = []
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            t = Task.parse(line)
            if t is not None:
                t.raw_index = idx
                out.append(t)
        return out

    def load(self) -> list[Task]:
        return self._read(self.active_path)

    def load_done(self) -> list[Task]:
        return self._read(self.done_path)

    def save(self, tasks: list[Task]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        body = "\n".join(t.serialize() for t in tasks)
        self.active_path.write_text(body + ("\n" if body else ""), encoding="utf-8")

    def append_done(self, tasks: list[Task]) -> None:
        if not tasks:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        existing = self.done_path.read_text(encoding="utf-8") if self.done_path.exists() else ""
        add = "\n".join(t.serialize() for t in tasks)
        self.done_path.write_text(existing + add + "\n", encoding="utf-8")

    def new_id(self, existing: set[str]) -> str:
        rng = random.Random()
        for _ in range(10000):
            cand = "".join(rng.choice(ID_ALPHABET) for _ in range(3))
            if cand not in existing:
                return cand
        # extremely unlikely fallback
        return "".join(rng.choice(ID_ALPHABET) for _ in range(6))


# ----------------------------------------------------------------------------- helpers
PRIO_COLORS = {"A": "31;1", "B": "33;1", "C": "36;1"}  # red, yellow, cyan


def color(s: str, code: str) -> str:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return s
    return f"\033[{code}m{s}\033[0m"


def find(tasks: list[Task], tid: str) -> Task | None:
    for t in tasks:
        if t.id == tid:
            return t
    return None


def fmt_task(t: Task, ref: dt.date | None = None) -> str:
    ref = ref or today()
    box = "x" if t.done else " "
    pri = f"({t.priority}) " if t.priority else ""
    pri = color(pri, PRIO_COLORS.get(t.priority or "", "0")) if t.priority else ""
    desc = t.description
    meta: list[str] = []
    if t.area:
        meta.append(color(t.area, "35"))            # magenta
    for p in t.projects:
        meta.append(color(f"+{p}", "34"))           # blue
    for c in t.contexts:
        meta.append(color(f"@{c}", "32"))           # green
    if t.due:
        days = (t.due - ref).days
        if t.done:
            tag = f"due:{iso(t.due)}"
        elif days < 0:
            tag = color(f"due:{iso(t.due)} (overdue {-days}d)", "31;1")
        elif days == 0:
            tag = color("due:today", "33;1")
        elif days == 1:
            tag = color("due:tomorrow", "33")
        else:
            tag = f"due:{iso(t.due)} ({days}d)"
        meta.append(tag)
    metastr = ("  " + "  ".join(meta)) if meta else ""
    idstr = color(f"[{t.id}]", "90")
    return f"{idstr} [{box}] {pri}{desc}{metastr}"


def sort_key(t: Task):
    pr = t.priority or "Z~"          # no priority sorts after Z
    due = t.due or dt.date.max
    return (pr, due, t.created or dt.date.max)


# ----------------------------------------------------------------------------- commands
def cmd_add(store: Store, args) -> int:
    tasks = store.load()
    ids = {t.id for t in tasks} | {t.id for t in store.load_done()}
    t = Task(description=" ".join(args.text).strip(), created=today())
    if not t.description:
        print("nothing to add (empty description)", file=sys.stderr)
        return 2
    if args.priority:
        t.priority = args.priority.upper()
    if args.area:
        t.kv["area"] = args.area
    if args.due:
        t.kv["due"] = resolve_due(args.due)
    for p in args.project or []:
        t.projects.append(p.lstrip("+"))
    for c in args.context or []:
        t.contexts.append(c.lstrip("@"))
    # inline +project / @context / key:val already in the text are parsed too
    inline = Task.parse(f"x {t.description}")  # cheap reparse to pull inline tags
    if inline:
        t.projects = list(dict.fromkeys(t.projects + inline.projects))
        t.contexts = list(dict.fromkeys(t.contexts + inline.contexts))
        for k, v in inline.kv.items():
            t.kv.setdefault(k, v)
        t.description = inline.description
    t.kv["id"] = store.new_id(ids)
    tasks.append(t)
    store.save(tasks)
    print("added " + fmt_task(t))
    return 0


def resolve_due(s: str) -> str:
    s = s.strip().lower()
    if s in ("today", "tod"):
        return iso(today())
    if s in ("tomorrow", "tom", "tmr"):
        return iso(today() + dt.timedelta(days=1))
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if s in weekdays:
        target = weekdays.index(s)
        delta = (target - today().weekday()) % 7
        delta = delta or 7
        return iso(today() + dt.timedelta(days=delta))
    m = re.match(r"^\+(\d+)d?$", s)
    if m:
        return iso(today() + dt.timedelta(days=int(m.group(1))))
    if DATE_RE.match(s):
        return s
    raise SystemExit(f"unrecognized due date: {s!r} (use YYYY-MM-DD, today, tomorrow, +Nd, or a weekday)")


def filtered(tasks: list[Task], args) -> list[Task]:
    out = tasks
    if getattr(args, "area", None):
        out = [t for t in out if t.area == args.area]
    if getattr(args, "project", None):
        out = [t for t in out if args.project.lstrip("+") in t.projects]
    if getattr(args, "context", None):
        out = [t for t in out if args.context.lstrip("@") in t.contexts]
    if getattr(args, "priority", None):
        out = [t for t in out if t.priority == args.priority.upper()]
    if getattr(args, "overdue", False):
        out = [t for t in out if t.overdue()]
    if getattr(args, "due_before", None):
        cutoff = dt.date.fromisoformat(resolve_due(args.due_before))
        out = [t for t in out if t.due and t.due <= cutoff]
    if getattr(args, "search", None):
        q = args.search.lower()
        out = [t for t in out if q in t.serialize().lower()]
    return out


def print_grouped(tasks: list[Task]) -> None:
    if not tasks:
        print(color("  (none)", "90"))
        return
    by_area: dict[str, list[Task]] = {}
    for t in tasks:
        by_area.setdefault(t.area or "unfiled", []).append(t)
    first = True
    for area in sorted(by_area, key=lambda a: (a == "unfiled", a)):
        if not first:
            print()
        first = False
        print(color(area.upper(), "1;4"))
        for t in sorted(by_area[area], key=sort_key):
            print("  " + fmt_task(t))


def cmd_list(store: Store, args) -> int:
    tasks = store.load()
    if not args.all:
        tasks = [t for t in tasks if not t.done]
    shown = filtered(tasks, args)
    print_grouped(shown)
    n = len([t for t in shown if not t.done])
    print(color(f"\n{n} task(s) shown", "90"))
    return 0


def cmd_today(store: Store, args) -> int:
    tasks = [t for t in store.load() if not t.done]
    ref = today()
    overdue = [t for t in tasks if t.overdue(ref)]
    due_today = [t for t in tasks if t.due == ref]
    flagged = [t for t in tasks if t.priority == "A" and t not in overdue and t not in due_today]
    print(color(f"AGENDA — {iso(ref)} ({ref.strftime('%A')})", "1;4"))
    if overdue:
        print("\n" + color("⚠ Overdue", "31;1"))
        for t in sorted(overdue, key=sort_key):
            print("  " + fmt_task(t, ref))
    print("\n" + color("Due today", "33;1"))
    if due_today:
        for t in sorted(due_today, key=sort_key):
            print("  " + fmt_task(t, ref))
    else:
        print(color("  (nothing due)", "90"))
    if flagged:
        print("\n" + color("Top priority (A)", "31"))
        for t in sorted(flagged, key=sort_key):
            print("  " + fmt_task(t, ref))
    total = len(overdue) + len(due_today) + len(flagged)
    print(color(f"\n{total} item(s) need attention today", "90"))
    return 0


def _mutate(store: Store, ids: list[str]):
    tasks = store.load()
    hits = [t for t in tasks if t.id in set(ids)]
    missing = set(ids) - {t.id for t in hits}
    if missing:
        print(f"unknown id(s): {', '.join(sorted(missing))}", file=sys.stderr)
    return tasks, hits


def cmd_done(store: Store, args) -> int:
    tasks, hits = _mutate(store, args.id)
    for t in hits:
        if not t.done:
            t.completed = today()
            print("done " + fmt_task(t))
    store.save(tasks)
    return 0 if hits else 1


def cmd_rm(store: Store, args) -> int:
    tasks, hits = _mutate(store, args.id)
    keep = [t for t in tasks if t not in hits]
    store.save(keep)
    for t in hits:
        print("removed " + fmt_task(t))
    return 0 if hits else 1


def cmd_pri(store: Store, args) -> int:
    tasks, hits = _mutate(store, [args.id])
    for t in hits:
        t.priority = None if args.priority in ("-", "none") else args.priority.upper()
        print("set priority " + fmt_task(t))
    store.save(tasks)
    return 0 if hits else 1


def cmd_edit(store: Store, args) -> int:
    tasks, hits = _mutate(store, [args.id])
    for t in hits:
        if args.due is not None:
            if args.due in ("-", "none", ""):
                t.kv.pop("due", None)
            else:
                t.kv["due"] = resolve_due(args.due)
        if args.area:
            t.kv["area"] = args.area
        if args.text:
            t.description = " ".join(args.text).strip()
        if args.project:
            t.projects = [p.lstrip("+") for p in args.project]
        if args.context:
            t.contexts = [c.lstrip("@") for c in args.context]
        print("edited " + fmt_task(t))
    store.save(tasks)
    return 0 if hits else 1


def cmd_archive(store: Store, args) -> int:
    tasks = store.load()
    done = [t for t in tasks if t.done]
    keep = [t for t in tasks if not t.done]
    store.append_done(done)
    store.save(keep)
    print(f"archived {len(done)} completed task(s) -> {store.done_path}")
    return 0


def cmd_areas(store: Store, args) -> int:
    tasks = [t for t in store.load() if not t.done]
    counts: dict[str, int] = {}
    for t in tasks:
        counts[t.area or "unfiled"] = counts.get(t.area or "unfiled", 0) + 1
    for a in sorted(counts):
        print(f"{counts[a]:>3}  {a}")
    return 0


def cmd_projects(store: Store, args) -> int:
    tasks = [t for t in store.load() if not t.done]
    counts: dict[str, int] = {}
    for t in tasks:
        for p in (t.projects or ["(no project)"]):
            counts[p] = counts.get(p, 0) + 1
    for p in sorted(counts, key=lambda k: (-counts[k], k)):
        print(f"{counts[p]:>3}  +{p}")
    return 0


def render_agenda_md(store: Store, ref: dt.date | None = None) -> str:
    ref = ref or today()
    tasks = [t for t in store.load() if not t.done]
    overdue = sorted([t for t in tasks if t.overdue(ref)], key=sort_key)
    due_today = sorted([t for t in tasks if t.due == ref], key=sort_key)
    soon = sorted(
        [t for t in tasks if t.due and ref < t.due <= ref + dt.timedelta(days=7)],
        key=sort_key,
    )
    flagged = sorted(
        [t for t in tasks if t.priority == "A" and not t.overdue(ref) and t.due != ref],
        key=sort_key,
    )

    def line(t: Task) -> str:
        bits = [t.description]
        if t.area:
            bits.append(f"_{t.area}_")
        for p in t.projects:
            bits.append(f"`+{p}`")
        if t.due:
            bits.append(f"(due {iso(t.due)})")
        return "- [ ] " + " ".join(bits)

    out = [f"# Agenda — {iso(ref)} ({ref.strftime('%A')})", ""]
    out.append(f"_{len(tasks)} open tasks · {len(overdue)} overdue · {len(due_today)} due today_")
    out.append("")
    if overdue:
        out += ["## ⚠️ Overdue", *[line(t) for t in overdue], ""]
    out += ["## Due today"]
    out += [line(t) for t in due_today] if due_today else ["_Nothing due today._"]
    out.append("")
    if flagged:
        out += ["## Top priority", *[line(t) for t in flagged], ""]
    if soon:
        out += ["## Next 7 days", *[line(t) for t in soon], ""]
    # area breakdown
    by_area: dict[str, int] = {}
    for t in tasks:
        by_area[t.area or "unfiled"] = by_area.get(t.area or "unfiled", 0) + 1
    if by_area:
        out += ["## Open by area"]
        out += [f"- **{a}**: {by_area[a]}" for a in sorted(by_area)]
        out.append("")
    out.append(f"<sub>Generated {iso(ref)} by tasks.py</sub>")
    return "\n".join(out) + "\n"


def cmd_agenda(store: Store, args) -> int:
    md = render_agenda_md(store)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"wrote agenda -> {args.out}")
    else:
        sys.stdout.write(md)
    return 0


# ----------------------------------------------------------------------------- cli
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tasks", description="business + personal task manager")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("add", help="add a task")
    a.add_argument("text", nargs="+")
    a.add_argument("-a", "--area", choices=AREAS)
    a.add_argument("-p", "--priority")
    a.add_argument("-d", "--due", help="YYYY-MM-DD | today | tomorrow | +Nd | weekday")
    a.add_argument("-P", "--project", action="append")
    a.add_argument("-c", "--context", action="append")
    a.set_defaults(func=cmd_add)

    for name, helptext in (("list", "list tasks"), ("ls", "list tasks")):
        l = sub.add_parser(name, help=helptext)
        l.add_argument("-a", "--area", choices=AREAS)
        l.add_argument("-P", "--project")
        l.add_argument("-c", "--context")
        l.add_argument("-p", "--priority")
        l.add_argument("--overdue", action="store_true")
        l.add_argument("--due-before", dest="due_before")
        l.add_argument("-s", "--search")
        l.add_argument("--all", action="store_true", help="include completed")
        l.set_defaults(func=cmd_list)

    for name in ("today", "agenda-tty"):
        t = sub.add_parser(name, help="today's agenda (terminal)")
        t.set_defaults(func=cmd_today)

    d = sub.add_parser("done", help="mark task(s) complete")
    d.add_argument("id", nargs="+")
    d.set_defaults(func=cmd_done)

    r = sub.add_parser("rm", help="delete task(s)")
    r.add_argument("id", nargs="+")
    r.set_defaults(func=cmd_rm)

    pr = sub.add_parser("pri", help="set/clear priority: tasks pri <id> <A-Z|->")
    pr.add_argument("id")
    pr.add_argument("priority")
    pr.set_defaults(func=cmd_pri)

    e = sub.add_parser("edit", help="edit a task's fields")
    e.add_argument("id")
    e.add_argument("text", nargs="*")
    e.add_argument("-a", "--area", choices=AREAS)
    e.add_argument("-d", "--due")
    e.add_argument("-P", "--project", action="append")
    e.add_argument("-c", "--context", action="append")
    e.set_defaults(func=cmd_edit)

    sub.add_parser("archive", help="move completed tasks to done.txt").set_defaults(func=cmd_archive)
    sub.add_parser("areas", help="open count by area").set_defaults(func=cmd_areas)
    sub.add_parser("projects", help="open count by project").set_defaults(func=cmd_projects)

    ag = sub.add_parser("agenda", help="render Markdown agenda (for mobile)")
    ag.add_argument("-o", "--out", help="write to file instead of stdout")
    ag.set_defaults(func=cmd_agenda)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        # default action: today's agenda then a hint
        cmd_today(Store(), args)
        return 0
    return args.func(Store(), args)


if __name__ == "__main__":
    raise SystemExit(main())
