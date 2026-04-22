#!/usr/bin/env python3
"""Terminal contacts manager.

Plain-text persistence. IDs are strictly monotonic across removals
(the "next id" counter is stored on disk and never decreases).

Storage layout (plain text, both files co-located):
  contacts.txt    one record per line:  <id>\t<name>\t<email>\t<phone>
  contacts.meta   one line: next_id=<int>

Tab is the field separator. Tabs and newlines in user input are
rejected at the input boundary so the on-disk format stays
unambiguous. A missing phone is stored as the literal empty string
(the tab is still present, giving four columns on every line).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


DEFAULT_DATA_DIR = os.environ.get(
    "CONTACTS_DIR",
    os.path.join(os.path.expanduser("~"), ".contacts"),
)
DATA_FILENAME = "contacts.txt"
META_FILENAME = "contacts.meta"
FIELD_SEP = "\t"
META_KEY = "next_id"


# ---------- data model ----------

@dataclass
class Contact:
    id: int
    name: str
    email: str
    phone: str = ""

    def to_line(self) -> str:
        return FIELD_SEP.join([str(self.id), self.name, self.email, self.phone])

    @classmethod
    def from_line(cls, line: str) -> "Contact":
        parts = line.rstrip("\n").split(FIELD_SEP)
        if len(parts) != 4:
            raise ValueError(f"malformed record (expected 4 fields): {line!r}")
        try:
            cid = int(parts[0])
        except ValueError as e:
            raise ValueError(f"malformed id in record: {line!r}") from e
        return cls(id=cid, name=parts[1], email=parts[2], phone=parts[3])

    def format_display(self) -> str:
        phone = self.phone if self.phone else "-"
        return f"[{self.id}] {self.name} <{self.email}> phone={phone}"


# ---------- store ----------

class ContactsStore:
    """Load / mutate / save the contacts list and the monotonic id counter."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.data_path = os.path.join(data_dir, DATA_FILENAME)
        self.meta_path = os.path.join(data_dir, META_FILENAME)
        self.contacts: List[Contact] = []
        self.next_id: int = 1
        self._load()

    # ---- persistence ----

    def _load(self) -> None:
        # Missing data dir / files is not an error — it's an empty store.
        if not os.path.isdir(self.data_dir):
            return
        if os.path.isfile(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                for raw in f:
                    if not raw.strip():
                        continue
                    self.contacts.append(Contact.from_line(raw))
        if os.path.isfile(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw or "=" not in raw:
                        continue
                    k, _, v = raw.partition("=")
                    if k.strip() == META_KEY:
                        try:
                            self.next_id = int(v.strip())
                        except ValueError:
                            pass
        # Self-heal: next_id must exceed every existing id.
        if self.contacts:
            max_seen = max(c.id for c in self.contacts)
            if self.next_id <= max_seen:
                self.next_id = max_seen + 1

    def _atomic_write(self, path: str, text: str) -> None:
        d = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def save(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)
        body = "".join(c.to_line() + "\n" for c in self.contacts)
        self._atomic_write(self.data_path, body)
        self._atomic_write(self.meta_path, f"{META_KEY}={self.next_id}\n")

    # ---- queries ----

    def get(self, cid: int) -> Optional[Contact]:
        for c in self.contacts:
            if c.id == cid:
                return c
        return None

    def find_by_email(self, email: str) -> Optional[Contact]:
        needle = email.strip().lower()
        for c in self.contacts:
            if c.email.lower() == needle:
                return c
        return None

    def search(self, query: str) -> List[Contact]:
        q = query.lower()
        out = []
        for c in self.contacts:
            if (
                q in c.name.lower()
                or q in c.email.lower()
                or q in c.phone.lower()
            ):
                out.append(c)
        return out

    def list_all(self) -> List[Contact]:
        return list(self.contacts)

    # ---- mutations ----

    def add(self, name: str, email: str, phone: str = "") -> Contact:
        _validate_field("name", name, required=True)
        _validate_field("email", email, required=True)
        _validate_field("phone", phone, required=False)
        if self.find_by_email(email) is not None:
            raise DuplicateError(f"a contact with email {email!r} already exists")
        c = Contact(id=self.next_id, name=name, email=email, phone=phone)
        self.contacts.append(c)
        self.next_id += 1  # monotonic; never reused even after removals
        return c

    def update(
        self,
        cid: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Contact:
        c = self.get(cid)
        if c is None:
            raise NotFoundError(f"no contact with id {cid}")
        if name is not None:
            _validate_field("name", name, required=True)
            c.name = name
        if email is not None:
            _validate_field("email", email, required=True)
            other = self.find_by_email(email)
            if other is not None and other.id != c.id:
                raise DuplicateError(
                    f"another contact already uses email {email!r} (id={other.id})"
                )
            c.email = email
        if phone is not None:
            _validate_field("phone", phone, required=False)
            c.phone = phone
        return c

    def remove(self, cid: int) -> Contact:
        for i, c in enumerate(self.contacts):
            if c.id == cid:
                del self.contacts[i]
                # next_id is NOT decremented — monotonic across removals.
                return c
        raise NotFoundError(f"no contact with id {cid}")


# ---------- errors ----------

class ContactsError(Exception):
    pass


class DuplicateError(ContactsError):
    pass


class NotFoundError(ContactsError):
    pass


class ValidationError(ContactsError):
    pass


def _validate_field(label: str, value: str, *, required: bool) -> None:
    if value is None:
        if required:
            raise ValidationError(f"{label} is required")
        return
    if required and value.strip() == "":
        raise ValidationError(f"{label} must not be empty")
    if "\t" in value or "\n" in value or "\r" in value:
        raise ValidationError(f"{label} must not contain tab or newline characters")


# ---------- CLI ----------

def _parse_id(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(f"id must be an integer, got {raw!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="contacts",
        description="Plain-text terminal contacts manager.",
    )
    p.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"directory for contacts.txt / contacts.meta (default: {DEFAULT_DATA_DIR})",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s_add = sub.add_parser("add", help="add a contact")
    s_add.add_argument("name")
    s_add.add_argument("email")
    s_add.add_argument("--phone", default="")

    sub.add_parser("list", help="list all contacts")

    s_find = sub.add_parser("find", help="substring search over name/email/phone")
    s_find.add_argument("query")

    s_up = sub.add_parser("update", help="update fields on an existing contact")
    s_up.add_argument("id")
    s_up.add_argument("--name")
    s_up.add_argument("--email")
    s_up.add_argument("--phone")

    s_rm = sub.add_parser("remove", help="remove a contact by id")
    s_rm.add_argument("id")

    return p


def run(argv: Optional[List[str]] = None, *, stdout=None, stderr=None) -> int:
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        store = ContactsStore(args.data_dir)

        if args.cmd == "add":
            c = store.add(args.name, args.email, args.phone or "")
            store.save()
            print(f"added {c.format_display()}", file=stdout)
            return 0

        if args.cmd == "list":
            contacts = store.list_all()
            if not contacts:
                print("(no contacts)", file=stdout)
                return 0
            for c in contacts:
                print(c.format_display(), file=stdout)
            return 0

        if args.cmd == "find":
            hits = store.search(args.query)
            if not hits:
                print("(no matches)", file=stdout)
                return 0
            for c in hits:
                print(c.format_display(), file=stdout)
            return 0

        if args.cmd == "update":
            cid = _parse_id(args.id)
            if args.name is None and args.email is None and args.phone is None:
                raise ValidationError(
                    "update requires at least one of --name / --email / --phone"
                )
            c = store.update(cid, name=args.name, email=args.email, phone=args.phone)
            store.save()
            print(f"updated {c.format_display()}", file=stdout)
            return 0

        if args.cmd == "remove":
            cid = _parse_id(args.id)
            c = store.remove(cid)
            store.save()
            print(f"removed {c.format_display()}", file=stdout)
            return 0

        parser.error(f"unknown command: {args.cmd}")
        return 2

    except ContactsError as e:
        print(f"error: {e}", file=stderr)
        return 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
