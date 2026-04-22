"""
storage.py — Read/write tasks to a plain-text file.

File format (one task per line):
    <id>|<status>|<text>

where <status> is either "[ ]" (pending) or "[x]" (done).

The delimiter inside <text> is escaped: a literal pipe character is stored
as the two-character sequence ``\|``.  A literal backslash is stored as
``\\``.  This makes serialize/deserialize a true identity for any text
including pipes, backslashes, whitespace, and unicode.

Atomic writes use a sibling temp file + os.replace so a crash cannot
produce a half-written tasks file.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple

# Internal line format: id|status|text
_DELIMITER = "|"
_STATUS_PENDING = "[ ]"
_STATUS_DONE = "[x]"


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _escape(text: str) -> str:
    """Escape backslashes and pipe characters in task text."""
    # Order matters: escape backslashes before pipes.
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _unescape(text: str) -> str:
    """Reverse _escape."""
    # Accumulate result to handle sequences correctly.
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            next_ch = text[i + 1]
            if next_ch == "\\":
                result.append("\\")
                i += 2
                continue
            elif next_ch == "|":
                result.append("|")
                i += 2
                continue
        result.append(text[i])
        i += 1
    return "".join(result)


def serialize(task_id: int, done: bool, text: str) -> str:
    """Return a single line (no newline) representing one task."""
    status = _STATUS_DONE if done else _STATUS_PENDING
    return f"{task_id}{_DELIMITER}{status}{_DELIMITER}{_escape(text)}"


def deserialize(line: str) -> Tuple[int, bool, str]:
    """
    Parse one line into (id, done, text).

    Splits on the *first two* unescaped pipe characters so that escaped pipes
    in the text are preserved correctly.
    """
    # We need to split on the first two literal (unescaped) '|' characters.
    # Walk character by character to find them.
    parts = []
    current: List[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] in ("\\", "|"):
            # Escaped sequence — keep as-is in the current field.
            current.append(ch)
            current.append(line[i + 1])
            i += 2
        elif ch == _DELIMITER and len(parts) < 2:
            parts.append("".join(current))
            current = []
            i += 1
        else:
            current.append(ch)
            i += 1
    parts.append("".join(current))

    if len(parts) < 3:
        raise ValueError(f"Malformed line: {line!r}")

    task_id = int(parts[0])
    raw_status = parts[1]
    raw_text = parts[2]

    if raw_status == _STATUS_DONE:
        done = True
    elif raw_status == _STATUS_PENDING:
        done = False
    else:
        raise ValueError(f"Unknown status {raw_status!r} in line: {line!r}")

    text = _unescape(raw_text)
    return task_id, done, text


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load(path: Path) -> List[Tuple[int, bool, str]]:
    """
    Load all tasks from *path*.

    Returns an empty list if the file does not exist.  Blank and malformed
    lines are silently skipped so that minor file corruption never prevents
    the tool from starting.
    """
    if not path.exists():
        return []

    tasks: List[Tuple[int, bool, str]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue  # skip blank lines
            try:
                tasks.append(deserialize(line))
            except (ValueError, IndexError):
                # Skip malformed lines; don't crash.
                continue
    return tasks


def save(path: Path, tasks: List[Tuple[int, bool, str]]) -> None:
    """
    Atomically write *tasks* to *path*.

    Creates the parent directory if it does not exist.
    Uses a sibling temp file + os.replace for crash safety.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file in the same directory so os.replace is atomic
    # (source and destination on the same filesystem).
    dir_ = str(path.parent)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for task_id, done, text in tasks:
                fh.write(serialize(task_id, done, text) + "\n")
        os.replace(tmp_path, str(path))
    except Exception:
        # Clean up the temp file if anything went wrong.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
