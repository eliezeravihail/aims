"""
tasks.py — Task model and in-memory CRUD.

A Task is a simple dataclass.  TaskManager wraps storage.py and exposes
the four operations the CLI needs: add, list, mark_complete, remove.

Id assignment:
    IDs are monotonically increasing integers.  The next id is always
    max(existing ids) + 1, defaulting to 1 when the list is empty.  Ids are
    NEVER reused after a task is removed.

Error types:
    InvalidIdError  — raised for non-numeric, negative, or unknown ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from . import storage


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    done: bool
    text: str

    def __str__(self) -> str:
        status = "[x]" if self.done else "[ ]"
        return f"{self.id:>4}  {status}  {self.text}"


class InvalidIdError(Exception):
    """
    Raised when a caller supplies an id that is non-numeric, negative,
    zero, or does not correspond to any existing task.
    """


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class TaskManager:
    """
    Manages tasks backed by a plain-text file.

    All mutating methods flush to disk immediately so that data is durable
    after every operation.
    """

    def __init__(self, data_path: Path) -> None:
        self._path = data_path
        self._tasks: List[Task] = []
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        raw = storage.load(self._path)
        self._tasks = [Task(id=tid, done=done, text=text) for tid, done, text in raw]

    def _save(self) -> None:
        storage.save(self._path, [(t.id, t.done, t.text) for t in self._tasks])

    def _next_id(self) -> int:
        if not self._tasks:
            return 1
        return max(t.id for t in self._tasks) + 1

    def _parse_id(self, raw_id: object) -> int:
        """
        Validate and return an integer task id.

        Accepts int or str.  Raises InvalidIdError for anything that is
        non-numeric, negative, or zero.
        """
        if isinstance(raw_id, str):
            if not raw_id.strip().lstrip("-").isdigit():
                raise InvalidIdError(f"'{raw_id}' is not a valid id (must be a positive integer).")
            value = int(raw_id.strip())
        elif isinstance(raw_id, int):
            value = raw_id
        else:
            raise InvalidIdError(f"'{raw_id}' is not a valid id.")

        if value <= 0:
            raise InvalidIdError(f"Id must be a positive integer, got {value}.")
        return value

    def _find(self, task_id: int) -> Task:
        for t in self._tasks:
            if t.id == task_id:
                return t
        raise InvalidIdError(f"No task with id {task_id}.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, text: str) -> Task:
        """Add a new pending task and persist immediately."""
        task = Task(id=self._next_id(), done=False, text=text)
        self._tasks.append(task)
        self._save()
        return task

    def list_tasks(self) -> List[Task]:
        """Return all tasks (snapshot; caller must not mutate)."""
        return list(self._tasks)

    def mark_complete(self, raw_id: object) -> Task:
        """
        Mark a task done.

        If the task is already done, this is a no-op (returns the task
        unchanged).  Raises InvalidIdError for bad ids.
        """
        task_id = self._parse_id(raw_id)
        task = self._find(task_id)
        if not task.done:
            task.done = True
            self._save()
        return task

    def remove(self, raw_id: object) -> Task:
        """
        Remove a task permanently.

        Raises InvalidIdError for bad ids.  Returns the removed task.
        """
        task_id = self._parse_id(raw_id)
        task = self._find(task_id)
        self._tasks = [t for t in self._tasks if t.id != task_id]
        self._save()
        return task
