"""Unit tests for todo.py. Run with: python -m unittest test_todo.py"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

# Make sibling module importable.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import todo  # noqa: E402


class TaskRoundTripTests(unittest.TestCase):
    def test_to_line_and_back(self):
        t = todo.Task(id=3, status="open",
                      created="2026-04-22T00:00:00Z",
                      description="buy milk")
        line = t.to_line()
        self.assertNotIn("\n", line)
        back = todo.Task.from_line(line + "\n")
        self.assertEqual(back, t)

    def test_escape_tabs_and_newlines(self):
        t = todo.Task(id=1, status="open",
                      created="2026-04-22T00:00:00Z",
                      description="line1\nline2\tindented")
        line = t.to_line()
        self.assertEqual(line.count("\n"), 0)
        self.assertEqual(line.count("\t"), 3)  # 3 real separators
        back = todo.Task.from_line(line)
        self.assertEqual(back.description, "line1\nline2\tindented")

    def test_malformed_line_raises(self):
        with self.assertRaises(ValueError):
            todo.Task.from_line("not-enough-fields\n")
        with self.assertRaises(ValueError):
            todo.Task.from_line("abc\topen\t2026-04-22T00:00:00Z\tdesc\n")
        with self.assertRaises(ValueError):
            todo.Task.from_line("1\tweird\t2026-04-22T00:00:00Z\tdesc\n")


class FileOpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "tasks.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *argv):
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = todo.main(["--file", self.path, *argv])
        return rc, buf_out.getvalue(), buf_err.getvalue()

    def test_missing_file_list_is_empty(self):
        rc, out, _ = self._run("list")
        self.assertEqual(rc, 0)
        self.assertIn("(no tasks)", out)

    def test_add_list_complete_remove_cycle(self):
        rc, out, _ = self._run("add", "write", "tests")
        self.assertEqual(rc, 0)
        self.assertIn("added #1", out)

        rc, out, _ = self._run("add", "ship", "it")
        self.assertIn("added #2", out)

        rc, out, _ = self._run("list")
        self.assertIn("write tests", out)
        self.assertIn("ship it", out)
        self.assertIn("[ ] 1", out)

        rc, out, _ = self._run("complete", "1")
        self.assertEqual(rc, 0)
        self.assertIn("completed #1", out)

        # Default list hides completed.
        rc, out, _ = self._run("list")
        self.assertNotIn("write tests", out)
        self.assertIn("ship it", out)

        rc, out, _ = self._run("list", "--all")
        self.assertIn("[x] 1", out)
        self.assertIn("[ ] 2", out)

        rc, out, _ = self._run("remove", "2")
        self.assertEqual(rc, 0)
        self.assertIn("removed #2", out)

        rc, out, _ = self._run("list", "--all")
        self.assertNotIn("ship it", out)

    def test_persistence_between_runs(self):
        self._run("add", "persistent", "task")
        # New invocation, fresh in-memory state.
        rc, out, _ = self._run("list")
        self.assertIn("persistent task", out)

    def test_invalid_id_complete(self):
        rc, _, err = self._run("complete", "42")
        self.assertEqual(rc, 1)
        self.assertIn("no task with id 42", err)

    def test_invalid_id_remove(self):
        rc, _, err = self._run("remove", "42")
        self.assertEqual(rc, 1)
        self.assertIn("no task with id 42", err)

    def test_empty_description_rejected(self):
        rc, _, err = self._run("add", "   ")
        self.assertEqual(rc, 2)
        self.assertIn("non-empty", err)

    def test_ids_monotonic_even_after_remove(self):
        self._run("add", "a")
        self._run("add", "b")
        self._run("remove", "2")
        rc, out, _ = self._run("add", "c")
        self.assertIn("added #3", out)  # max + 1, not reused

    def test_complete_twice_is_noop(self):
        self._run("add", "x")
        self._run("complete", "1")
        rc, out, _ = self._run("complete", "1")
        self.assertEqual(rc, 0)
        self.assertIn("already complete", out)

    def test_malformed_line_is_skipped(self):
        # Hand-craft a file with one bad line and one good line.
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("garbage line with no tabs\n")
            fh.write("7\topen\t2026-04-22T00:00:00Z\tsurvivor\n")
        rc, out, err = self._run("list")
        self.assertEqual(rc, 0)
        self.assertIn("survivor", out)
        self.assertIn("malformed", err)

    def test_clear(self):
        self._run("add", "one")
        self._run("add", "two")
        rc, _, _ = self._run("clear")
        self.assertEqual(rc, 0)
        rc, out, _ = self._run("list", "--all")
        self.assertIn("(no tasks)", out)


if __name__ == "__main__":
    unittest.main()
