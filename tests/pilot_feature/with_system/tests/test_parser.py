"""
Tests for storage serialize/deserialize (parser layer).

Covers:
  - deserialize_task: Parse a well-formed line into correct id, status, text
  - serialize_task: Round-trip serialize then deserialize with field-for-field equality
  - property: serialize->deserialize is identity for arbitrary descriptions
"""

import pytest
import sys

sys.path.insert(0, "/tmp/todo_pilot/with_system")

from todo.storage import serialize, deserialize


class TestDeserializeTask:
    """Parse a well-formed line into a Task object with correct id, status, and description."""

    def test_pending_task_fields(self):
        line = "1|[ ]|Buy groceries"
        task_id, done, text = deserialize(line)
        assert task_id == 1
        assert done is False
        assert text == "Buy groceries"

    def test_done_task_fields(self):
        line = "42|[x]|Write unit tests"
        task_id, done, text = deserialize(line)
        assert task_id == 42
        assert done is True
        assert text == "Write unit tests"

    def test_description_with_spaces(self):
        line = "7|[ ]|  leading and trailing spaces  "
        task_id, done, text = deserialize(line)
        assert task_id == 7
        assert done is False
        assert text == "  leading and trailing spaces  "

    def test_malformed_line_raises_value_error(self):
        with pytest.raises((ValueError, IndexError)):
            deserialize("no delimiters here")

    def test_unknown_status_raises_value_error(self):
        with pytest.raises(ValueError):
            deserialize("1|[?]|Some text")


class TestSerializeTask:
    """Round-trip: serialize a Task then deserialize it and assert field-for-field equality."""

    def test_pending_round_trip(self):
        original = (5, False, "Buy milk")
        line = serialize(*original)
        result = deserialize(line)
        assert result == original

    def test_done_round_trip(self):
        original = (10, True, "Finish project")
        line = serialize(*original)
        result = deserialize(line)
        assert result == original

    def test_round_trip_with_pipe_in_text(self):
        original = (3, False, "a|b|c")
        line = serialize(*original)
        result = deserialize(line)
        assert result == original

    def test_round_trip_with_backslash_in_text(self):
        original = (4, False, "path\\to\\file")
        line = serialize(*original)
        result = deserialize(line)
        assert result == original

    def test_round_trip_combined_special_chars(self):
        original = (99, True, "back\\slash and pipe|here")
        line = serialize(*original)
        result = deserialize(line)
        assert result == original


class TestSerializeDeserializeProperty:
    """
    Property-style tests: for arbitrary descriptions (whitespace, punctuation, unicode),
    serialize->deserialize is identity.
    """

    @pytest.mark.parametrize("description", [
        "",
        "   ",
        "\t\n\r",
        "hello | world",
        "back\\slash",
        "pipe|and\\backslash|together",
        "Unicode: 中文 éàü",
        "Emoji: \U0001f600\U0001f4dd",
        "Mixed: α|beta\\gamma|δ",
        "!@#$%^&*()_+-=[]{}';:\",.<>?/`~",
        "  leading spaces",
        "trailing spaces  ",
        "line\nwith\nnewlines",
    ])
    def test_identity_for_various_descriptions(self, description):
        task_id = 1
        done = False
        line = serialize(task_id, done, description)
        result_id, result_done, result_text = deserialize(line)
        assert result_id == task_id
        assert result_done == done
        assert result_text == description
