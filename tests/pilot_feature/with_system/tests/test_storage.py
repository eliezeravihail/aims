"""
Tests for storage.load and storage.save (file I/O layer).

Covers:
  - load_tasks: Returns empty list when data file does not exist
  - load_tasks: Skips blank lines and non-matching lines without raising
  - save_tasks: Save then load cycle preserves count, ids, statuses, and descriptions
  - regression: File with only blank lines -> empty list, no exception
"""

import sys
import pytest

sys.path.insert(0, "/tmp/todo_pilot/with_system")

from todo import storage


class TestLoadTasksFileMissing:
    """Load returns empty list when data file does not exist."""

    def test_nonexistent_file_returns_empty_list(self, tmp_path):
        path = tmp_path / "does_not_exist.txt"
        result = storage.load(path)
        assert result == []

    def test_returns_list_type(self, tmp_path):
        path = tmp_path / "nope.txt"
        result = storage.load(path)
        assert isinstance(result, list)


class TestLoadTasksSkipsBadLines:
    """Load skips blank lines and lines that do not match the expected format without raising."""

    def test_blank_lines_are_skipped(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text("1|[ ]|First task\n\n\n2|[x]|Second task\n", encoding="utf-8")
        result = storage.load(path)
        assert len(result) == 2

    def test_malformed_line_is_skipped(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text(
            "1|[ ]|Valid task\nNOT A VALID LINE\n2|[x]|Another valid task\n",
            encoding="utf-8",
        )
        result = storage.load(path)
        assert len(result) == 2
        ids = [r[0] for r in result]
        assert 1 in ids
        assert 2 in ids

    def test_no_exception_on_entirely_malformed_file(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text("garbage\nmore garbage\n!!!\n", encoding="utf-8")
        result = storage.load(path)
        assert result == []

    def test_mixed_valid_blank_malformed(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text(
            "1|[ ]|Good\n\nbadline\n   \n2|[x]|Also good\n",
            encoding="utf-8",
        )
        result = storage.load(path)
        assert len(result) == 2


class TestSaveLoadCycle:
    """Save then load cycle preserves count, ids, statuses, and descriptions for a mixed list."""

    def test_mixed_list_round_trip(self, tmp_path):
        path = tmp_path / "tasks.txt"
        tasks = [
            (1, False, "Pending task"),
            (2, True, "Done task"),
            (3, False, "Another pending"),
        ]
        storage.save(path, tasks)
        loaded = storage.load(path)
        assert len(loaded) == len(tasks)
        for original, result in zip(tasks, loaded):
            assert result[0] == original[0], f"id mismatch: {result} vs {original}"
            assert result[1] == original[1], f"status mismatch: {result} vs {original}"
            assert result[2] == original[2], f"text mismatch: {result} vs {original}"

    def test_empty_list_saves_and_loads(self, tmp_path):
        path = tmp_path / "tasks.txt"
        storage.save(path, [])
        loaded = storage.load(path)
        assert loaded == []

    def test_single_task_round_trip(self, tmp_path):
        path = tmp_path / "tasks.txt"
        tasks = [(7, True, "Only task")]
        storage.save(path, tasks)
        loaded = storage.load(path)
        assert loaded == tasks

    def test_special_chars_round_trip(self, tmp_path):
        path = tmp_path / "tasks.txt"
        tasks = [(1, False, "task|with|pipes"), (2, True, "task\\with\\backslashes")]
        storage.save(path, tasks)
        loaded = storage.load(path)
        assert loaded == tasks


class TestRegressionOnlyBlankLines:
    """File exists but contains only blank lines; empty list, no exception."""

    def test_only_blank_lines_returns_empty(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text("\n\n\n   \n\t\n", encoding="utf-8")
        result = storage.load(path)
        assert result == []

    def test_single_blank_line_returns_empty(self, tmp_path):
        path = tmp_path / "tasks.txt"
        path.write_text("\n", encoding="utf-8")
        result = storage.load(path)
        assert result == []
