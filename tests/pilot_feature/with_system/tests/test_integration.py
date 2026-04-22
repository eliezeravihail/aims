"""
Integration tests: storage + task_manager working together end-to-end
(within the same process).

Covers:
  - Add tasks, save to file, reload from file, assert identical
  - Load a file with mix of valid/blank/malformed lines; only valid tasks returned
  - Mark complete then save then reload; completed status persists
  - Remove then save then reload; removed task absent, others intact
"""

import sys
import pytest

sys.path.insert(0, "/tmp/todo_pilot/with_system")

from todo.tasks import TaskManager
from todo import storage


def make_manager(tmp_path):
    return TaskManager(tmp_path / "tasks.txt")


class TestAddSaveReload:
    """Add tasks, save to file, reload from file, assert task list is identical."""

    def test_task_list_identical_after_reload(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        mgr.add("First")
        mgr.add("Second")
        mgr.add("Third")

        # Reload from same path
        mgr2 = TaskManager(path)
        tasks = mgr2.list_tasks()
        assert len(tasks) == 3
        assert tasks[0].text == "First"
        assert tasks[1].text == "Second"
        assert tasks[2].text == "Third"
        assert all(not t.done for t in tasks)

    def test_ids_persist_across_reload(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        t1 = mgr.add("A")
        t2 = mgr.add("B")

        mgr2 = TaskManager(path)
        tasks = mgr2.list_tasks()
        assert tasks[0].id == t1.id
        assert tasks[1].id == t2.id


class TestLoadMixedFile:
    """Load a file with mix of valid/blank/malformed lines; only valid tasks returned."""

    def test_only_valid_tasks_loaded(self, tmp_path):
        path = tmp_path / "tasks.txt"
        # Write a file directly with valid, blank, and malformed lines
        path.write_text(
            "1|[ ]|Valid task one\n"
            "\n"
            "NOT|A|VALID|TASK|LINE|WITH|TOO|MANY|PIPES\n"
            "   \n"
            "2|[x]|Valid task two\n"
            "completely_malformed\n"
            "3|[ ]|Valid task three\n",
            encoding="utf-8",
        )
        mgr = TaskManager(path)
        tasks = mgr.list_tasks()
        assert len(tasks) == 3
        ids = {t.id for t in tasks}
        assert ids == {1, 2, 3}

    def test_statuses_loaded_correctly(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text(
            "1|[ ]|Pending\n"
            "garbage line\n"
            "2|[x]|Done\n",
            encoding="utf-8",
        )
        mgr = TaskManager(path)
        tasks = mgr.list_tasks()
        status_map = {t.id: t.done for t in tasks}
        assert status_map[1] is False
        assert status_map[2] is True


class TestMarkCompletePersists:
    """Mark complete then save then reload; completed status persists."""

    def test_done_status_persists_after_reload(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        t1 = mgr.add("Pending task")
        t2 = mgr.add("Another task")
        mgr.mark_complete(t1.id)

        mgr2 = TaskManager(path)
        tasks = mgr2.list_tasks()
        status_map = {t.id: t.done for t in tasks}
        assert status_map[t1.id] is True
        assert status_map[t2.id] is False

    def test_all_done_persists(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        tasks = [mgr.add(f"Task {i}") for i in range(3)]
        for t in tasks:
            mgr.mark_complete(t.id)

        mgr2 = TaskManager(path)
        reloaded = mgr2.list_tasks()
        assert all(t.done for t in reloaded)


class TestRemoveThenReload:
    """Remove then save then reload; removed task absent, others intact."""

    def test_removed_task_absent_after_reload(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        t1 = mgr.add("Keep me")
        t2 = mgr.add("Remove me")
        t3 = mgr.add("Keep me too")
        mgr.remove(t2.id)

        mgr2 = TaskManager(path)
        tasks = mgr2.list_tasks()
        ids = {t.id for t in tasks}
        assert t2.id not in ids
        assert t1.id in ids
        assert t3.id in ids

    def test_remaining_tasks_intact_after_reload(self, tmp_path):
        path = tmp_path / "tasks.txt"
        mgr = TaskManager(path)
        t1 = mgr.add("Alpha")
        t2 = mgr.add("Beta")
        t3 = mgr.add("Gamma")
        mgr.remove(t1.id)

        mgr2 = TaskManager(path)
        tasks = mgr2.list_tasks()
        assert len(tasks) == 2
        texts = [t.text for t in tasks]
        assert "Alpha" not in texts
        assert "Beta" in texts
        assert "Gamma" in texts
