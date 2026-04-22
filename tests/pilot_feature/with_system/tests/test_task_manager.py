"""
Tests for TaskManager (tasks.py) — add, mark_complete, remove, list_tasks.

All tests use tmp_path for isolation and never touch any shared file.
"""

import sys
import pytest

sys.path.insert(0, "/tmp/todo_pilot/with_system")

from todo.tasks import Task, TaskManager, InvalidIdError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager(tmp_path):
    return TaskManager(tmp_path / "tasks.txt")


# ---------------------------------------------------------------------------
# add_task
# ---------------------------------------------------------------------------

class TestAddTaskEmpty:
    """Adding a task to an empty list produces id=1 and pending status."""

    def test_first_task_has_id_one(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("My first task")
        assert task.id == 1

    def test_first_task_is_pending(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("My first task")
        assert task.done is False

    def test_first_task_description_matches(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Hello world")
        assert task.text == "Hello world"


class TestAddTaskSuccessive:
    """Adding successive tasks produces monotonically increasing ids with no duplicates."""

    def test_successive_ids_increase(self, tmp_path):
        mgr = make_manager(tmp_path)
        t1 = mgr.add("First")
        t2 = mgr.add("Second")
        t3 = mgr.add("Third")
        assert t1.id < t2.id < t3.id

    def test_successive_ids_no_duplicates(self, tmp_path):
        mgr = make_manager(tmp_path)
        tasks = [mgr.add(f"Task {i}") for i in range(5)]
        ids = [t.id for t in tasks]
        assert len(ids) == len(set(ids)), "Duplicate ids found"

    def test_five_successive_ids_are_unique(self, tmp_path):
        mgr = make_manager(tmp_path)
        ids = [mgr.add(f"T{i}").id for i in range(5)]
        assert sorted(ids) == list(range(ids[0], ids[0] + 5))


# ---------------------------------------------------------------------------
# mark_complete
# ---------------------------------------------------------------------------

class TestMarkCompletePending:
    """Mark a pending task complete; assert status transitions to done."""

    def test_pending_becomes_done(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Do the thing")
        assert task.done is False
        marked = mgr.mark_complete(task.id)
        assert marked.done is True

    def test_list_reflects_done_status(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Do the thing")
        mgr.mark_complete(task.id)
        tasks = mgr.list_tasks()
        assert tasks[0].done is True


class TestMarkCompleteAlreadyDone:
    """Mark an already-complete task complete; assert no error and status remains done."""

    def test_idempotent_mark_no_error(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Already done")
        mgr.mark_complete(task.id)
        # Second call should not raise
        result = mgr.mark_complete(task.id)
        assert result.done is True

    def test_status_remains_done(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Still done")
        mgr.mark_complete(task.id)
        mgr.mark_complete(task.id)
        tasks = mgr.list_tasks()
        assert tasks[0].done is True


class TestMarkCompleteNonNumericId:
    """Mark with a non-numeric id string; assert a well-typed error is raised."""

    def test_alpha_string_raises_invalid_id_error(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete("abc")

    def test_empty_string_raises_invalid_id_error(self, tmp_path):
        mgr = make_manager(tmp_path)
        with pytest.raises(InvalidIdError):
            mgr.mark_complete("")

    def test_float_string_raises_invalid_id_error(self, tmp_path):
        mgr = make_manager(tmp_path)
        with pytest.raises(InvalidIdError):
            mgr.mark_complete("1.5")


class TestMarkCompleteOutOfRangeId:
    """Mark with an out-of-range positive integer id; assert a well-typed error is raised."""

    def test_nonexistent_positive_id_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete(9999)

    def test_id_beyond_max_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        t = mgr.add("Only task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete(t.id + 100)


class TestMarkCompleteNegativeId:
    """Mark with a negative integer id; assert a well-typed error is raised."""

    def test_negative_int_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete(-1)

    def test_negative_string_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete("-1")

    def test_zero_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.mark_complete(0)


# ---------------------------------------------------------------------------
# remove_task
# ---------------------------------------------------------------------------

class TestRemoveTaskSingleItem:
    """Remove the only task from a single-item list; assert list is empty afterward."""

    def test_list_empty_after_remove(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Only task")
        mgr.remove(task.id)
        assert mgr.list_tasks() == []

    def test_remove_returns_the_task(self, tmp_path):
        mgr = make_manager(tmp_path)
        task = mgr.add("Only task")
        removed = mgr.remove(task.id)
        assert removed.id == task.id
        assert removed.text == task.text


class TestRemoveTaskOutOfRange:
    """Remove with an out-of-range id; assert a well-typed error and list is unchanged."""

    def test_out_of_range_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.remove(9999)

    def test_list_unchanged_after_failed_remove(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task A")
        mgr.add("Task B")
        count_before = len(mgr.list_tasks())
        with pytest.raises(InvalidIdError):
            mgr.remove(9999)
        assert len(mgr.list_tasks()) == count_before


class TestRemoveTaskNonNumericId:
    """Remove with a non-numeric id string; assert a well-typed error is raised."""

    def test_alpha_string_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.add("Task")
        with pytest.raises(InvalidIdError):
            mgr.remove("xyz")

    def test_empty_string_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        with pytest.raises(InvalidIdError):
            mgr.remove("")


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------

class TestListTasksEmpty:
    """List tasks when internal list is empty; assert returns empty sequence without error."""

    def test_empty_returns_empty_list(self, tmp_path):
        mgr = make_manager(tmp_path)
        result = mgr.list_tasks()
        assert result == []

    def test_empty_does_not_raise(self, tmp_path):
        mgr = make_manager(tmp_path)
        # Should not raise
        mgr.list_tasks()


class TestListTasksOrder:
    """List tasks returns all tasks in stable insertion order with correct statuses."""

    def test_insertion_order_preserved(self, tmp_path):
        mgr = make_manager(tmp_path)
        texts = ["Alpha", "Beta", "Gamma", "Delta"]
        for t in texts:
            mgr.add(t)
        result = mgr.list_tasks()
        assert [t.text for t in result] == texts

    def test_statuses_correct_after_mix(self, tmp_path):
        mgr = make_manager(tmp_path)
        t1 = mgr.add("Task 1")
        t2 = mgr.add("Task 2")
        t3 = mgr.add("Task 3")
        mgr.mark_complete(t2.id)
        tasks = mgr.list_tasks()
        status_map = {t.id: t.done for t in tasks}
        assert status_map[t1.id] is False
        assert status_map[t2.id] is True
        assert status_map[t3.id] is False

    def test_count_matches_adds(self, tmp_path):
        mgr = make_manager(tmp_path)
        for i in range(7):
            mgr.add(f"Task {i}")
        assert len(mgr.list_tasks()) == 7
