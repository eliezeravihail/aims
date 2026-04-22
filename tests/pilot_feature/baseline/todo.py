#!/usr/bin/env python3
"""Terminal TODO-list application.

Stores tasks in a plain-text file. The file may begin with an optional
header line:

    # next_id=<n>

followed by task records, one per line, each of the form:

    <id>\t<status>\t<created_iso>\t<description>

where:
    - <id>          integer, unique, monotonically assigned; never reused.
    - <status>      "open" or "done".
    - <created_iso> ISO-8601 timestamp (UTC) when the task was added.
    - <description> free text. Tabs and newlines are escaped so the record
                    stays on a single line.

Any line starting with '#' is treated as a comment; only the first
`next_id=` comment is honored.

The default data file is ~/.todo_pilot_tasks.txt, overridable with
--file / $TODO_FILE.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional

DEFAULT_FILE = os.environ.get(
    "TODO_FILE",
    os.path.join(os.path.expanduser("~"), ".todo_pilot_tasks.txt"),
)

STATUS_OPEN = "open"
STATUS_DONE = "done"
VALID_STATUS = {STATUS_OPEN, STATUS_DONE}


# ---------- data model ----------

@dataclass
class Task:
    id: int
    status: str
    created: str
    description: str

    def to_line(self) -> str:
        return "\t".join(
            [
                str(self.id),
                self.status,
                self.created,
                _escape(self.description),
            ]
        )

    @classmethod
    def from_line(cls, line: str) -> "Task":
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 4:
            raise ValueError(f"malformed task record: {line!r}")
        tid_s, status, created, desc = parts
        try:
            tid = int(tid_s)
        except ValueError as exc:
            raise ValueError(f"bad id in record: {line!r}") from exc
        if status not in VALID_STATUS:
            raise ValueError(f"bad status in record: {line!r}")
        return cls(id=tid, status=status, created=created,
                   description=_unescape(desc))


def _escape(s: str) -> str:
    # Keep records single-line and tab-delimited.
    return (
        s.replace("\\", "\\\\")
         .replace("\t", "\\t")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
    )


def _unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == "\\":
                out.append("\\")
            elif nxt == "t":
                out.append("\t")
            elif nxt == "n":
                out.append("\n")
            elif nxt == "r":
                out.append("\r")
            else:
                out.append(nxt)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---------- persistence ----------

HEADER_PREFIX = "# next_id="


def load_state(path: str) -> tuple[List[Task], int]:
    """Load (tasks, next_id) from `path`. Missing file -> ([], 1)."""
    if not os.path.exists(path):
        return [], 1
    tasks: List[Task] = []
    next_id: Optional[int] = None
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                if next_id is None and stripped.startswith(HEADER_PREFIX):
                    try:
                        next_id = int(stripped[len(HEADER_PREFIX):].strip())
                    except ValueError:
                        print(
                            f"warning: bad header on line {lineno} in {path}",
                            file=sys.stderr,
                        )
                continue
            try:
                tasks.append(Task.from_line(raw))
            except ValueError as exc:
                print(
                    f"warning: skipping malformed line {lineno} in {path}: "
                    f"{exc}",
                    file=sys.stderr,
                )
    if next_id is None:
        # Legacy file with no header: derive from max id.
        next_id = (max((t.id for t in tasks), default=0)) + 1
    else:
        # Self-heal if header is somehow behind reality.
        highest = max((t.id for t in tasks), default=0)
        if next_id <= highest:
            next_id = highest + 1
    return tasks, next_id


def save_state(path: str, tasks: Iterable[Task], next_id: int) -> None:
    """Atomic write: write to tmp, then rename."""
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(f"{HEADER_PREFIX}{next_id}\n")
        for t in tasks:
            fh.write(t.to_line() + "\n")
    os.replace(tmp, path)


# ---------- operations ----------

def _find(tasks: List[Task], tid: int) -> Optional[Task]:
    for t in tasks:
        if t.id == tid:
            return t
    return None


def cmd_add(path: str, description: str) -> int:
    description = description.strip()
    if not description:
        print("error: description must be non-empty", file=sys.stderr)
        return 2
    tasks, next_id = load_state(path)
    task = Task(
        id=next_id,
        status=STATUS_OPEN,
        created=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description=description,
    )
    tasks.append(task)
    save_state(path, tasks, next_id + 1)
    print(f"added #{task.id}: {task.description}")
    return 0


def cmd_list(path: str, show_all: bool) -> int:
    tasks, _ = load_state(path)
    if not tasks:
        print("(no tasks)")
        return 0
    visible = tasks if show_all else [t for t in tasks if t.status == STATUS_OPEN]
    if not visible:
        print("(no open tasks; use --all to include completed)")
        return 0
    # Column width for id.
    width = max(len(str(t.id)) for t in visible)
    for t in visible:
        mark = "x" if t.status == STATUS_DONE else " "
        print(f"[{mark}] {t.id:>{width}}  {t.description}")
    return 0


def cmd_complete(path: str, tid: int) -> int:
    tasks, next_id = load_state(path)
    task = _find(tasks, tid)
    if task is None:
        print(f"error: no task with id {tid}", file=sys.stderr)
        return 1
    if task.status == STATUS_DONE:
        print(f"#{tid} already complete")
        return 0
    task.status = STATUS_DONE
    save_state(path, tasks, next_id)
    print(f"completed #{tid}: {task.description}")
    return 0


def cmd_remove(path: str, tid: int) -> int:
    tasks, next_id = load_state(path)
    task = _find(tasks, tid)
    if task is None:
        print(f"error: no task with id {tid}", file=sys.stderr)
        return 1
    tasks = [t for t in tasks if t.id != tid]
    save_state(path, tasks, next_id)
    print(f"removed #{tid}: {task.description}")
    return 0


def cmd_clear(path: str) -> int:
    # Reset tasks; keep next_id counter so ids remain monotonic across clears.
    _, next_id = load_state(path)
    save_state(path, [], next_id)
    print("cleared all tasks")
    return 0


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="todo",
        description="Plain-text terminal TODO list.",
    )
    p.add_argument(
        "--file", "-f",
        default=DEFAULT_FILE,
        help=f"path to tasks file (default: {DEFAULT_FILE})",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a task")
    a.add_argument("description", nargs="+", help="task description")

    ls = sub.add_parser("list", help="list tasks")
    ls.add_argument("--all", "-a", action="store_true",
                    help="include completed tasks")

    c = sub.add_parser("complete", help="mark a task complete")
    c.add_argument("id", type=int)

    r = sub.add_parser("remove", help="remove a task")
    r.add_argument("id", type=int)

    sub.add_parser("clear", help="remove all tasks")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = args.file

    if args.cmd == "add":
        return cmd_add(path, " ".join(args.description))
    if args.cmd == "list":
        return cmd_list(path, show_all=args.all)
    if args.cmd == "complete":
        return cmd_complete(path, args.id)
    if args.cmd == "remove":
        return cmd_remove(path, args.id)
    if args.cmd == "clear":
        return cmd_clear(path)

    parser.error(f"unknown command: {args.cmd}")
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
