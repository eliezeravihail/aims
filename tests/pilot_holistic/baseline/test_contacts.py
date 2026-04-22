"""Tests for the contacts manager."""

from __future__ import annotations

import io
import os
import unittest

from contacts import (
    Contact,
    ContactsStore,
    DuplicateError,
    NotFoundError,
    ValidationError,
    run,
)


class _TmpDir:
    """Tiny context manager that avoids pulling in pytest fixtures."""

    def __init__(self, base: str):
        self.base = base
        self.path = None

    def __enter__(self) -> str:
        import tempfile

        self.path = tempfile.mkdtemp(prefix="contacts-test-", dir=self.base)
        return self.path

    def __exit__(self, exc_type, exc, tb) -> None:
        import shutil

        if self.path and os.path.isdir(self.path):
            shutil.rmtree(self.path)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._base = tempfile.mkdtemp(prefix="contacts-root-")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._base, ignore_errors=True)

    def test_missing_dir_is_empty_store(self):
        # Directory that does not exist -> load as empty, no crash.
        path = os.path.join(self._base, "nope-does-not-exist")
        store = ContactsStore(path)
        self.assertEqual(store.list_all(), [])
        self.assertEqual(store.next_id, 1)

    def test_add_and_list(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("Ada", "ada@example.com", "555-0001")
            s.add("Bea", "bea@example.com")
            self.assertEqual([c.id for c in s.list_all()], [1, 2])
            self.assertEqual(s.next_id, 3)

    def test_duplicate_email_rejected(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("Ada", "ada@example.com")
            with self.assertRaises(DuplicateError):
                s.add("Other", "ADA@example.com")  # case-insensitive

    def test_find_substring(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("Ada Lovelace", "ada@example.com", "555-0001")
            s.add("Bea Arthur", "bea@example.com", "555-0002")
            by_name = s.search("lovelace")
            by_email = s.search("bea@")
            by_phone = s.search("0002")
            self.assertEqual([c.id for c in by_name], [1])
            self.assertEqual([c.id for c in by_email], [2])
            self.assertEqual([c.id for c in by_phone], [2])

    def test_update_fields(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("Ada", "ada@example.com")
            s.update(1, name="Ada L.", phone="555-9999")
            c = s.get(1)
            self.assertEqual(c.name, "Ada L.")
            self.assertEqual(c.phone, "555-9999")

    def test_update_email_duplicate_rejected(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("Ada", "ada@example.com")
            s.add("Bea", "bea@example.com")
            with self.assertRaises(DuplicateError):
                s.update(2, email="ada@example.com")

    def test_update_invalid_id(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            with self.assertRaises(NotFoundError):
                s.update(42, name="Ghost")

    def test_remove_invalid_id(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            with self.assertRaises(NotFoundError):
                s.remove(42)

    def test_ids_monotonic_across_removals(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("A", "a@example.com")
            s.add("B", "b@example.com")
            s.add("C", "c@example.com")
            s.remove(2)
            s.remove(3)
            s.remove(1)
            self.assertEqual(s.list_all(), [])
            new = s.add("D", "d@example.com")
            self.assertEqual(new.id, 4)
            self.assertEqual(s.next_id, 5)

    def test_persist_and_reload_preserves_monotonic_counter(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            s.add("A", "a@example.com")
            s.add("B", "b@example.com")
            s.remove(1)
            s.remove(2)
            s.save()
            # Reload from disk; counter must NOT reset.
            s2 = ContactsStore(d)
            self.assertEqual(s2.list_all(), [])
            self.assertEqual(s2.next_id, 3)
            c = s2.add("C", "c@example.com")
            self.assertEqual(c.id, 3)

    def test_validation_rejects_tab_and_newline(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            with self.assertRaises(ValidationError):
                s.add("bad\tname", "x@example.com")
            with self.assertRaises(ValidationError):
                s.add("ok", "bad\nemail@example.com")

    def test_empty_name_rejected(self):
        with _TmpDir(self._base) as d:
            s = ContactsStore(d)
            with self.assertRaises(ValidationError):
                s.add("   ", "x@example.com")

    def test_record_roundtrip(self):
        c = Contact(id=7, name="Z", email="z@example.com", phone="1")
        line = c.to_line()
        back = Contact.from_line(line + "\n")
        self.assertEqual(back, c)


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._d = tempfile.mkdtemp(prefix="contacts-cli-")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._d, ignore_errors=True)

    def _run(self, *args):
        out, err = io.StringIO(), io.StringIO()
        rc = run(
            ["--data-dir", self._d, *args],
            stdout=out,
            stderr=err,
        )
        return rc, out.getvalue(), err.getvalue()

    def test_list_empty(self):
        rc, out, _ = self._run("list")
        self.assertEqual(rc, 0)
        self.assertIn("no contacts", out)

    def test_end_to_end(self):
        rc, _, _ = self._run("add", "Ada", "ada@example.com", "--phone", "555-1")
        self.assertEqual(rc, 0)
        rc, _, _ = self._run("add", "Bea", "bea@example.com")
        self.assertEqual(rc, 0)

        # duplicate email -> exit 1
        rc, _, err = self._run("add", "Again", "ada@example.com")
        self.assertEqual(rc, 1)
        self.assertIn("already exists", err)

        rc, out, _ = self._run("find", "bea")
        self.assertIn("bea@example.com", out)

        rc, _, _ = self._run("update", "1", "--phone", "555-9")
        self.assertEqual(rc, 0)
        rc, out, _ = self._run("list")
        self.assertIn("555-9", out)

        rc, _, _ = self._run("remove", "1")
        self.assertEqual(rc, 0)
        rc, _, _ = self._run("remove", "2")
        self.assertEqual(rc, 0)
        rc, out, _ = self._run("list")
        self.assertIn("no contacts", out)

        # Next add must get id 3 (monotonic across drain).
        rc, out, _ = self._run("add", "Cal", "cal@example.com")
        self.assertIn("[3]", out)


if __name__ == "__main__":
    unittest.main()
