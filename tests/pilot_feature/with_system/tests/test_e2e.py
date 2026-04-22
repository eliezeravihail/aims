"""
End-to-end tests for the CLI entry point (python -m todo).

Covers:
  - Run add, list, done, remove as subprocess; assert stdout + exit codes
  - Persistence across separate process invocations
  - Non-numeric id on done/remove subcommands; non-zero exit, stderr message
  - List with no data file or empty list; exit 0, empty-state message
"""

import subprocess
import sys
import os
import pytest


def run_todo(args, data_file, **kwargs):
    """Run `python -m todo --data-file <data_file> <args>` as a subprocess."""
    cmd = [sys.executable, "-m", "todo", "--data-file", str(data_file)] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/tmp/todo_pilot/with_system",
        **kwargs,
    )
    return result


class TestAddListDoneRemoveSubcommands:
    """Run add, list, done, remove as subprocess; assert stdout + exit codes."""

    def test_add_exits_zero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        result = run_todo(["add", "My task"], data_file)
        assert result.returncode == 0

    def test_add_stdout_contains_added(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        result = run_todo(["add", "My task"], data_file)
        assert "Added" in result.stdout or "My task" in result.stdout

    def test_list_after_add_shows_task(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Grocery run"], data_file)
        result = run_todo(["list"], data_file)
        assert result.returncode == 0
        assert "Grocery run" in result.stdout

    def test_done_exits_zero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        add_result = run_todo(["add", "Task to complete"], data_file)
        # Extract id from output
        # The format is: Added:    1  [ ]  Task to complete
        # We assume id=1 for the first task in an empty list
        result = run_todo(["done", "1"], data_file)
        assert result.returncode == 0

    def test_done_stdout_contains_marked(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Finish report"], data_file)
        result = run_todo(["done", "1"], data_file)
        assert "done" in result.stdout.lower() or "[x]" in result.stdout

    def test_remove_exits_zero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "To be removed"], data_file)
        result = run_todo(["remove", "1"], data_file)
        assert result.returncode == 0

    def test_remove_stdout_contains_removed(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Remove me"], data_file)
        result = run_todo(["remove", "1"], data_file)
        assert "Removed" in result.stdout or "Remove me" in result.stdout

    def test_list_after_remove_empty(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Single task"], data_file)
        run_todo(["remove", "1"], data_file)
        result = run_todo(["list"], data_file)
        assert result.returncode == 0
        # Task should be gone
        assert "Single task" not in result.stdout


class TestPersistenceAcrossProcesses:
    """Persistence across separate process invocations."""

    def test_task_survives_second_invocation(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Persistent task"], data_file)
        # New process
        result = run_todo(["list"], data_file)
        assert result.returncode == 0
        assert "Persistent task" in result.stdout

    def test_multiple_tasks_persist(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Task Alpha"], data_file)
        run_todo(["add", "Task Beta"], data_file)
        run_todo(["add", "Task Gamma"], data_file)
        result = run_todo(["list"], data_file)
        assert "Task Alpha" in result.stdout
        assert "Task Beta" in result.stdout
        assert "Task Gamma" in result.stdout

    def test_done_status_persists_across_processes(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Complete me"], data_file)
        run_todo(["done", "1"], data_file)
        result = run_todo(["list"], data_file)
        assert "[x]" in result.stdout

    def test_removal_persists_across_processes(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Stay"], data_file)
        run_todo(["add", "Go away"], data_file)
        run_todo(["remove", "2"], data_file)
        result = run_todo(["list"], data_file)
        assert "Go away" not in result.stdout
        assert "Stay" in result.stdout


class TestNonNumericIdErrors:
    """Non-numeric id on done/remove subcommands; non-zero exit, stderr message."""

    def test_done_non_numeric_exits_nonzero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Some task"], data_file)
        result = run_todo(["done", "abc"], data_file)
        assert result.returncode != 0

    def test_done_non_numeric_has_stderr_message(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Some task"], data_file)
        result = run_todo(["done", "abc"], data_file)
        assert result.stderr.strip() != ""

    def test_remove_non_numeric_exits_nonzero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Some task"], data_file)
        result = run_todo(["remove", "xyz"], data_file)
        assert result.returncode != 0

    def test_remove_non_numeric_has_stderr_message(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Some task"], data_file)
        result = run_todo(["remove", "xyz"], data_file)
        assert result.stderr.strip() != ""

    def test_done_negative_exits_nonzero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Some task"], data_file)
        result = run_todo(["done", "-5"], data_file)
        assert result.returncode != 0


class TestListEmptyState:
    """List with no data file or empty list; exit 0, empty-state message."""

    def test_list_no_file_exits_zero(self, tmp_path):
        data_file = tmp_path / "nonexistent_tasks.txt"
        result = run_todo(["list"], data_file)
        assert result.returncode == 0

    def test_list_no_file_has_empty_state_message(self, tmp_path):
        data_file = tmp_path / "nonexistent_tasks.txt"
        result = run_todo(["list"], data_file)
        # Should print a friendly empty-state message
        assert result.stdout.strip() != ""

    def test_list_after_all_removed_exits_zero(self, tmp_path):
        data_file = tmp_path / "tasks.txt"
        run_todo(["add", "Task"], data_file)
        run_todo(["remove", "1"], data_file)
        result = run_todo(["list"], data_file)
        assert result.returncode == 0

    def test_list_empty_state_message_content(self, tmp_path):
        data_file = tmp_path / "fresh.txt"
        result = run_todo(["list"], data_file)
        # The CLI prints "No tasks yet. Use 'todo add <text>' to create one."
        assert "No tasks" in result.stdout or "no tasks" in result.stdout.lower()
