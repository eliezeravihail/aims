"""
cli.py — argparse entry point for the TODO CLI.

Commands
--------
  add <text>     Add a new task.
  list           Print all tasks (or a friendly message if none).
  done <id>      Mark task <id> as complete.
  remove <id>    Remove task <id> permanently.

Exit codes
----------
  0   Success (including empty list, already-done no-op).
  1   User error (invalid id, unknown id, missing argument).
  2   Unexpected internal error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .tasks import InvalidIdError, TaskManager

# Default storage location (inside the package directory's parent).
_DEFAULT_DATA_FILE = Path("/tmp/todo_pilot/with_system/tasks.txt")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple terminal TODO-list manager.",
    )
    parser.add_argument(
        "--data-file",
        metavar="PATH",
        default=str(_DEFAULT_DATA_FILE),
        help="Path to the plain-text storage file (default: %(default)s).",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # add
    p_add = subparsers.add_parser("add", help="Add a new task.")
    p_add.add_argument("text", nargs="+", help="Task description (words joined with spaces).")

    # list
    subparsers.add_parser("list", help="List all tasks.")

    # done
    p_done = subparsers.add_parser("done", help="Mark a task as complete.")
    p_done.add_argument("id", help="Task id.")

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove a task.")
    p_remove.add_argument("id", help="Task id.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Parse *argv* (defaults to sys.argv[1:]), run the command, and return
    an integer exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    data_path = Path(args.data_file)
    manager = TaskManager(data_path)

    try:
        if args.command == "add":
            text = " ".join(args.text)
            task = manager.add(text)
            print(f"Added: {task}")

        elif args.command == "list":
            tasks = manager.list_tasks()
            if not tasks:
                print("No tasks yet. Use 'todo add <text>' to create one.")
            else:
                for task in tasks:
                    print(task)

        elif args.command == "done":
            task = manager.mark_complete(args.id)
            print(f"Marked done: {task}")

        elif args.command == "remove":
            task = manager.remove(args.id)
            print(f"Removed: {task}")

    except InvalidIdError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2

    return 0


def entry_point() -> None:
    """Console-script entry point (calls sys.exit with the return code)."""
    sys.exit(main())
