#!/usr/bin/env python3
"""Terminal contacts manager.

Storage: plain text files, tab-separated, one contact per line.

Data file: contacts.tsv
  Format per line: <id>\t<name>\t<email>\t<phone>
  - phone may be empty (empty string between trailing tab)
  - name/email/phone are sanitised: tabs and newlines stripped

Counter file: contacts.counter
  Holds the next id to assign. Strictly monotonic across removals:
  removing id 3 does NOT free id 3; the next add uses 4, then 5, etc.

CLI:
  add <name> <email> [--phone <phone>]
  list
  find <query>
  update <id> [--name <name>] [--email <email>] [--phone <phone>]
  remove <id>
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Storage paths (overridable via env for tests)
# ---------------------------------------------------------------------------

DEFAULT_DIR = Path(os.environ.get("CONTACTS_DIR", Path(__file__).resolve().parent))
DATA_FILE = DEFAULT_DIR / "contacts.tsv"
COUNTER_FILE = DEFAULT_DIR / "contacts.counter"

FIELD_SEP = "\t"
RECORD_SEP = "\n"


# ---------------------------------------------------------------------------
# Record type
# ---------------------------------------------------------------------------


class Contact:
    __slots__ = ("id", "name", "email", "phone")

    def __init__(self, id: int, name: str, email: str, phone: str = "") -> None:
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone

    def to_line(self) -> str:
        return FIELD_SEP.join(
            [str(self.id), self.name, self.email, self.phone]
        )

    @classmethod
    def from_line(cls, line: str) -> "Contact":
        parts = line.rstrip("\n").split(FIELD_SEP)
        if len(parts) < 3:
            raise ValueError(f"malformed contact line: {line!r}")
        # Pad phone if absent (older-format tolerance).
        while len(parts) < 4:
            parts.append("")
        id_str, name, email, phone = parts[0], parts[1], parts[2], parts[3]
        try:
            id_val = int(id_str)
        except ValueError as e:
            raise ValueError(f"malformed contact id in line: {line!r}") from e
        return cls(id_val, name, email, phone)

    def __repr__(self) -> str:  # pragma: no cover - debug only
        return f"Contact(id={self.id}, name={self.name!r}, email={self.email!r}, phone={self.phone!r})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitise(value: str) -> str:
    """Strip characters that would corrupt TSV storage."""
    if value is None:
        return ""
    # Disallow tab / newline / carriage return in stored fields.
    return (
        value.replace("\t", " ")
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def _ensure_dir() -> None:
    DEFAULT_DIR.mkdir(parents=True, exist_ok=True)


def _load_all() -> List[Contact]:
    """Load all contacts. Missing file is treated as empty list."""
    if not DATA_FILE.exists():
        return []
    out: List[Contact] = []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        for raw in f:
            if not raw.strip():
                continue
            out.append(Contact.from_line(raw))
    return out


def _save_all(contacts: Iterable[Contact]) -> None:
    _ensure_dir()
    tmp = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for c in contacts:
            f.write(c.to_line() + RECORD_SEP)
    os.replace(tmp, DATA_FILE)


def _read_counter() -> int:
    """Return the next id to assign.

    If the counter file is missing, derive from existing data: 1 + max(id).
    Counter is strictly monotonic; callers must never decrement it.
    """
    if COUNTER_FILE.exists():
        try:
            return int(COUNTER_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            pass  # fall through to derivation
    contacts = _load_all()
    if not contacts:
        return 1
    return max(c.id for c in contacts) + 1


def _write_counter(n: int) -> None:
    _ensure_dir()
    tmp = COUNTER_FILE.with_suffix(COUNTER_FILE.suffix + ".tmp")
    tmp.write_text(str(n), encoding="utf-8")
    os.replace(tmp, COUNTER_FILE)


def _find_by_id(contacts: List[Contact], id_val: int) -> Optional[int]:
    for i, c in enumerate(contacts):
        if c.id == id_val:
            return i
    return None


def _email_exists(contacts: List[Contact], email: str, exclude_id: Optional[int] = None) -> bool:
    needle = email.lower()
    for c in contacts:
        if exclude_id is not None and c.id == exclude_id:
            continue
        if c.email.lower() == needle:
            return True
    return False


def _format_contact(c: Contact) -> str:
    phone_part = f"  phone={c.phone}" if c.phone else ""
    return f"[{c.id}] {c.name} <{c.email}>{phone_part}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_add(args: argparse.Namespace) -> int:
    name = _sanitise(args.name)
    email = _sanitise(args.email)
    phone = _sanitise(args.phone or "")

    if not name:
        print("error: name must be non-empty", file=sys.stderr)
        return 2
    if not email:
        print("error: email must be non-empty", file=sys.stderr)
        return 2

    contacts = _load_all()
    if _email_exists(contacts, email):
        print(f"error: duplicate email: {email}", file=sys.stderr)
        return 2

    next_id = _read_counter()
    new = Contact(next_id, name, email, phone)
    contacts.append(new)
    _save_all(contacts)
    _write_counter(next_id + 1)
    print(_format_contact(new))
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    contacts = _load_all()
    if not contacts:
        print("(no contacts)")
        return 0
    # Deterministic display order: by id ascending.
    for c in sorted(contacts, key=lambda x: x.id):
        print(_format_contact(c))
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    query = (args.query or "").lower()
    if not query:
        print("error: find requires a non-empty query", file=sys.stderr)
        return 2
    contacts = _load_all()
    hits = [
        c for c in sorted(contacts, key=lambda x: x.id)
        if query in c.name.lower()
        or query in c.email.lower()
        or query in c.phone.lower()
    ]
    if not hits:
        print("(no matches)")
        return 0
    for c in hits:
        print(_format_contact(c))
    return 0


def _parse_id(raw: str) -> Optional[int]:
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return None
    if val < 1:
        return None
    return val


def cmd_update(args: argparse.Namespace) -> int:
    id_val = _parse_id(args.id)
    if id_val is None:
        print(f"error: invalid id: {args.id}", file=sys.stderr)
        return 2

    contacts = _load_all()
    idx = _find_by_id(contacts, id_val)
    if idx is None:
        print(f"error: no contact with id {id_val}", file=sys.stderr)
        return 2

    target = contacts[idx]
    new_name = _sanitise(args.name) if args.name is not None else target.name
    new_email = _sanitise(args.email) if args.email is not None else target.email
    new_phone = _sanitise(args.phone) if args.phone is not None else target.phone

    if args.name is not None and not new_name:
        print("error: name must be non-empty", file=sys.stderr)
        return 2
    if args.email is not None and not new_email:
        print("error: email must be non-empty", file=sys.stderr)
        return 2

    if args.email is not None and _email_exists(contacts, new_email, exclude_id=id_val):
        print(f"error: duplicate email: {new_email}", file=sys.stderr)
        return 2

    if (
        args.name is None
        and args.email is None
        and args.phone is None
    ):
        print("error: update requires at least one of --name/--email/--phone", file=sys.stderr)
        return 2

    target.name = new_name
    target.email = new_email
    target.phone = new_phone
    _save_all(contacts)
    print(_format_contact(target))
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    id_val = _parse_id(args.id)
    if id_val is None:
        print(f"error: invalid id: {args.id}", file=sys.stderr)
        return 2

    contacts = _load_all()
    idx = _find_by_id(contacts, id_val)
    if idx is None:
        print(f"error: no contact with id {id_val}", file=sys.stderr)
        return 2

    removed = contacts.pop(idx)
    _save_all(contacts)
    # Note: counter is NOT decremented. IDs remain strictly monotonic.
    print(f"removed [{removed.id}] {removed.name}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="contacts",
        description="Terminal contacts manager (plain-text storage).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new contact.")
    p_add.add_argument("name")
    p_add.add_argument("email")
    p_add.add_argument("--phone", default=None)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all contacts.")
    p_list.set_defaults(func=cmd_list)

    p_find = sub.add_parser("find", help="Find contacts matching a query.")
    p_find.add_argument("query")
    p_find.set_defaults(func=cmd_find)

    p_update = sub.add_parser("update", help="Update a contact by id.")
    p_update.add_argument("id")
    p_update.add_argument("--name", default=None)
    p_update.add_argument("--email", default=None)
    p_update.add_argument("--phone", default=None)
    p_update.set_defaults(func=cmd_update)

    p_remove = sub.add_parser("remove", help="Remove a contact by id.")
    p_remove.add_argument("id")
    p_remove.set_defaults(func=cmd_remove)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OSError as e:
        print(f"error: io failure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
