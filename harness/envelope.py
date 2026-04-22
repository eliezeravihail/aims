"""Envelope parsing and validation.

An envelope is the single structured value every agent returns. The executor
reads *only* the envelope — never the agent's internal reasoning. Keeping
envelope parsing strict is how context isolation stays honest.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import SCHEMA_VERSION

_SCHEMA_DIR = Path(__file__).parent.parent / "schemas"


@dataclass(frozen=True)
class Envelope:
    """Canonical envelope. Exactly one of outputs/retry/abort is populated."""
    ok: bool
    outputs: dict | None = None
    retry: dict | None = None
    abort: dict | None = None
    advisory: str | None = None
    meta: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @property
    def signal(self) -> str:
        if self.ok and self.outputs is not None:
            return "ok"
        if self.retry is not None:
            return "retry"
        if self.abort is not None:
            return "abort"
        return "malformed"


class EnvelopeError(ValueError):
    """Raised when an envelope cannot be parsed or fails schema validation."""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_validator: Draft202012Validator | None = None


def _load_validator() -> Draft202012Validator:
    global _validator
    if _validator is None:
        schema = json.loads((_SCHEMA_DIR / "envelope.v1.json").read_text())
        _validator = Draft202012Validator(schema)
    return _validator


def extract_json(text: str) -> dict:
    """Tolerant JSON extractor.

    LLMs sometimes wrap JSON in code fences or leading prose. We accept:
      - a raw JSON object
      - a ```json ... ``` block
      - a ``` ... ``` block (with or without the json tag)
      - text that starts with '{' and ends with the matching '}'
    """
    text = text.strip()
    if not text:
        raise EnvelopeError("empty envelope")
    # fenced code block
    m = _JSON_BLOCK.search(text)
    if m:
        text = m.group(1)
    # plain JSON
    if not text.startswith("{"):
        raise EnvelopeError(f"envelope is not a JSON object: {text[:60]!r}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnvelopeError(f"invalid JSON: {exc.msg}") from exc


def parse(text_or_dict: str | dict) -> Envelope:
    """Parse + schema-validate an envelope. Raises EnvelopeError on failure."""
    raw = text_or_dict if isinstance(text_or_dict, dict) else extract_json(text_or_dict)
    # Add schema_version if the agent omitted it (lenient about this one field)
    raw.setdefault("schema_version", SCHEMA_VERSION)
    errors = sorted(_load_validator().iter_errors(raw), key=lambda e: e.path)
    if errors:
        msgs = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:3])
        raise EnvelopeError(f"schema violation: {msgs}")
    return Envelope(
        ok=raw["ok"],
        outputs=raw.get("outputs"),
        retry=raw.get("retry"),
        abort=raw.get("abort"),
        advisory=raw.get("advisory"),
        meta=raw.get("meta", {}),
        raw=raw,
    )


def ok(outputs: dict, advisory: str | None = None) -> dict:
    env = {"schema_version": SCHEMA_VERSION, "ok": True, "outputs": outputs}
    if advisory:
        env["advisory"] = advisory
    return env


def retry(reason: str, hint: str = "") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "retry": {"reason": reason, **({"hint": hint} if hint else {})},
    }


def abort(reason: str) -> dict:
    return {"schema_version": SCHEMA_VERSION, "ok": False, "abort": {"reason": reason}}
