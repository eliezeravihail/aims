import json

import pytest

from harness import envelope as env
from harness import SCHEMA_VERSION


def test_ok_helper_validates():
    e = env.parse(env.ok({"x": 1}))
    assert e.ok is True
    assert e.signal == "ok"
    assert e.outputs == {"x": 1}


def test_retry_helper_validates():
    e = env.parse(env.retry("bad input", hint="pass X"))
    assert e.ok is False
    assert e.signal == "retry"
    assert e.retry["reason"] == "bad input"
    assert e.retry["hint"] == "pass X"


def test_abort_helper_validates():
    e = env.parse(env.abort("unrecoverable"))
    assert e.signal == "abort"


def test_extract_json_unfenced():
    text = '{"schema_version":1,"ok":true,"outputs":{}}'
    assert env.parse(text).ok is True


def test_extract_json_fenced():
    text = '```json\n{"schema_version":1,"ok":true,"outputs":{"a":1}}\n```'
    assert env.parse(text).outputs == {"a": 1}


def test_extract_json_bare_fence():
    text = '```\n{"schema_version":1,"ok":true,"outputs":{}}\n```'
    assert env.parse(text).ok is True


def test_extract_json_strict_about_prose_prefix():
    text = "Here is the envelope:\n" + env_text(env.ok({}))
    # leading prose without a fence should fail — strict is the point
    with pytest.raises(env.EnvelopeError):
        env.parse(text)


def test_missing_schema_version_is_tolerated():
    """Missing schema_version is added automatically; everything else strict."""
    text = '{"ok":true,"outputs":{"y":2}}'
    assert env.parse(text).outputs == {"y": 2}


def test_multiple_signals_rejected():
    raw = {
        "schema_version": 1,
        "ok": False,
        "retry": {"reason": "x"},
        "abort": {"reason": "y"},
    }
    with pytest.raises(env.EnvelopeError):
        env.parse(raw)


def test_outputs_requires_ok_true():
    raw = {"schema_version": 1, "ok": False, "outputs": {}}
    with pytest.raises(env.EnvelopeError):
        env.parse(raw)


def test_advisory_is_allowed():
    raw = env.ok({"a": 1}, advisory="project-context-missing")
    e = env.parse(raw)
    assert e.advisory == "project-context-missing"


def test_empty_text_raises():
    with pytest.raises(env.EnvelopeError):
        env.parse("")


def env_text(d: dict) -> str:
    return json.dumps(d)
