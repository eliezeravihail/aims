"""Feature-flag resolution: decide whether a flag is on for a given user.

A :class:`Resolver` holds rules. Asked about a (flag, user) pair, every rule either abstains or
returns a :class:`Verdict` — an answer plus the authority it carries. The strongest verdict wins;
if no rule answers, the feature is off.

    >>> resolver = Resolver([Percentage("search", 50), BlockList("search", ["u7"])])
    >>> resolver.is_enabled("search", "u7")
    False

The ordering of verdicts is a published product rule and lives in exactly one place
(:meth:`Verdict.outranks`): an explicit list outranks a percentage rollout, and within the same
authority "off" outranks "on" — which is what makes a block beat an allow. A new kind of rule
declares the authority it speaks with and needs no change to :class:`Resolver`.

Some rules — :class:`ScheduledRollout` — speak about a moment in time, so a question is asked
at an instant: ``is_enabled(flag, user_id, now=None)``, defaulting to the wall clock. The instant
is resolved once per question and handed to every rule, so one answer is never assembled from two
different clock readings, and a caller can pin the clock to make a test say something definite.
"""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Optional

__all__ = [
    "Resolver",
    "Rule",
    "Verdict",
    "Authority",
    "Percentage",
    "ScheduledRollout",
    "AllowList",
    "BlockList",
]

#: Buckets a user can fall into for a percentage rollout. 10_000 buckets means a rollout can be
#: expressed down to 0.01%, which is the granularity early rollouts are actually run at.
_BUCKETS = 10_000


def _checked_percent(value: float, name: str) -> float:
    """Return ``value`` as a valid percentage, or raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100, got {value}")
    return value


def _checked_epoch_seconds(value: int, name: str) -> int:
    """Return ``value`` as a valid integer epoch-second timestamp, or raise."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be integer epoch seconds, got {type(value).__name__}")
    return value


def _resolve_now(now: Optional[float]) -> float:
    """Turn a caller's ``now`` (or its absence) into the single instant a question is asked at."""
    if now is None:
        return time.time()
    if isinstance(now, bool) or not isinstance(now, (int, float)):
        raise TypeError(f"now must be epoch seconds or None, got {type(now).__name__}")
    return now


class Authority(IntEnum):
    """How much weight a verdict carries. Higher wins."""

    ROLLOUT = 1
    """Spoken by a percentage rollout: a statement about a population."""

    EXPLICIT = 2
    """Spoken about this user by name."""


@dataclass(frozen=True)
class Verdict:
    """One rule's answer about one (flag, user) pair.

    A rule that has nothing to say returns ``None`` instead of a verdict, so "off" is a real
    answer with an owner rather than the absence of one.
    """

    enabled: bool
    authority: Authority

    def outranks(self, other: "Verdict") -> bool:
        """Whether this verdict beats ``other``.

        The single home of the precedence rule: an explicit statement about a user beats a
        statement about a population, and among equals the restrictive answer wins (so a block
        beats an allow, and any pair of conflicting rules resolves the same way whatever order
        they were given in).
        """
        if self.authority is not other.authority:
            return self.authority > other.authority
        return other.enabled and not self.enabled


class Rule(ABC):
    """A statement about one flag. Rules are immutable and free of state between calls.

    A rule is asked at an instant: ``now`` is epoch seconds, and omitting it means the wall clock.
    Rules that do not speak about time ignore it, so the answer for such a rule is the same at
    every instant.
    """

    @abstractmethod
    def verdict_for(
        self, flag: str, user_id: str, now: Optional[float] = None
    ) -> Optional[Verdict]:
        """Return this rule's verdict for the pair at ``now``, or ``None`` if it does not apply."""


class _FlagRule(Rule):
    """A rule scoped to a single flag; it abstains on every other flag."""

    def __init__(self, flag: str) -> None:
        if not isinstance(flag, str):
            raise TypeError(f"flag must be a string, got {type(flag).__name__}")
        self._flag = flag

    @property
    def flag(self) -> str:
        return self._flag

    def verdict_for(
        self, flag: str, user_id: str, now: Optional[float] = None
    ) -> Optional[Verdict]:
        if flag != self._flag:
            return None
        return self._verdict_for_own_flag(user_id, _resolve_now(now))

    @abstractmethod
    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        """Return the verdict for a user of this rule's own flag at ``now``, or ``None``."""


class _BucketRollout(_FlagRule):
    """A rollout that selects users by stable bucket; subclasses say what percentage is live.

    A user's bucket is derived from the flag and the user id alone —
    ``int.from_bytes(sha256(f"{flag}:{user_id}")[:8], "big") % 10_000`` — and the flag is on when
    that bucket is below ``percent`` of the bucket space. That derivation is part of the contract,
    not an implementation detail: it is what makes the same user get the same answer in another
    process, on another machine, and after a restart, and it is why the built-in ``hash()`` (salted
    per process) cannot be used. It is shared by every rollout rule, so widening a percentage only
    ever adds users — including when the widening happens over time, and including when a flag
    moves from one rollout rule to another.
    """

    def _verdict_at_percent(self, percent: float, user_id: str) -> Verdict:
        on = self._bucket_of(user_id) < percent * (_BUCKETS / 100)
        return Verdict(enabled=on, authority=Authority.ROLLOUT)

    def _bucket_of(self, user_id: str) -> int:
        digest = hashlib.sha256(f"{self._flag}:{user_id}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % _BUCKETS


class Percentage(_BucketRollout):
    """Turn a flag on for ``percent`` of users, stably.

    The selection follows the bucket contract of :class:`_BucketRollout`, and does not depend on
    when the question is asked.
    """

    def __init__(self, flag: str, percent: float) -> None:
        super().__init__(flag)
        self._percent = _checked_percent(percent, "percent")

    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        return self._verdict_at_percent(self._percent, user_id)

    def __repr__(self) -> str:
        return f"Percentage({self.flag!r}, {self._percent!r})"


class ScheduledRollout(_BucketRollout):
    """Ramp a flag from ``start_percent`` to ``end_percent`` across ``[start_at, end_at)``.

    Before ``start_at`` the rule behaves exactly like ``Percentage(flag, start_percent)``; at or
    after ``end_at``, exactly like ``Percentage(flag, end_percent)``; in between the live
    percentage moves linearly between the two. ``start_at`` and ``end_at`` are epoch seconds, and
    an empty window (``start_at == end_at``) is a clean switch from one percentage to the other.

    Users are picked by the same bucket as any other rollout, so a ramp is a nest of ever-wider
    sets rather than a reshuffle: a user the feature reaches at one instant keeps it for the rest
    of an upward ramp, and asking twice at the same instant always gives the same answer. That is
    also why an upward ramp can be swapped in for the ``Percentage`` rule it grows out of without
    moving anybody.
    """

    def __init__(
        self,
        flag: str,
        start_percent: float,
        end_percent: float,
        start_at: int,
        end_at: int,
    ) -> None:
        super().__init__(flag)
        self._start_percent = _checked_percent(start_percent, "start_percent")
        self._end_percent = _checked_percent(end_percent, "end_percent")
        self._start_at = _checked_epoch_seconds(start_at, "start_at")
        self._end_at = _checked_epoch_seconds(end_at, "end_at")
        if self._end_at < self._start_at:
            raise ValueError(
                f"end_at must not precede start_at, got {self._start_at} and {self._end_at}"
            )

    def percent_at(self, now: Optional[float] = None) -> float:
        """The percentage this rollout is live for at ``now`` (default: the wall clock)."""
        instant = _resolve_now(now)
        if instant < self._start_at:
            return self._start_percent
        if instant >= self._end_at:
            return self._end_percent
        elapsed = (instant - self._start_at) / (self._end_at - self._start_at)
        return self._start_percent + (self._end_percent - self._start_percent) * elapsed

    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        return self._verdict_at_percent(self.percent_at(now), user_id)

    def __repr__(self) -> str:
        return (
            f"ScheduledRollout({self.flag!r}, {self._start_percent!r}, {self._end_percent!r}, "
            f"{self._start_at!r}, {self._end_at!r})"
        )


class _MembershipRule(_FlagRule):
    """Named users get a fixed answer; everyone else is none of this rule's business."""

    _VERDICT_FOR_MEMBERS: Verdict

    def __init__(self, flag: str, user_ids: Iterable[str]) -> None:
        super().__init__(flag)
        if isinstance(user_ids, str):
            raise TypeError("user_ids must be a collection of ids, not a single string")
        self._user_ids = frozenset(user_ids)

    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        if user_id not in self._user_ids:
            return None
        return self._VERDICT_FOR_MEMBERS

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.flag!r}, {sorted(self._user_ids)!r})"


class AllowList(_MembershipRule):
    """The flag is on for exactly these users, whatever a rollout says."""

    _VERDICT_FOR_MEMBERS = Verdict(enabled=True, authority=Authority.EXPLICIT)


class BlockList(_MembershipRule):
    """The flag is off for exactly these users, whatever any other rule says."""

    _VERDICT_FOR_MEMBERS = Verdict(enabled=False, authority=Authority.EXPLICIT)


class Resolver:
    """Answers "is this flag on for this user?" from a fixed set of rules.

    The rules are captured at construction, and the answer for a given pair does not depend on the
    order the rules were given in. It can depend on when the question is asked, but only through
    the rules that say so: with no scheduled rule in play the answer never changes.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules = tuple(rules)
        for rule in self._rules:
            if not isinstance(rule, Rule):
                raise TypeError(f"not a rule: {rule!r}")

    def is_enabled(self, flag: str, user_id: str, now: Optional[float] = None) -> bool:
        """Whether ``flag`` is on for ``user_id`` at ``now`` (epoch seconds; default: right now).

        The strongest verdict among the rules that apply decides it. A flag no rule speaks about
        is off. The instant is resolved once here and passed to every rule, so all the rules
        behind one answer are speaking about the same moment.
        """
        instant = _resolve_now(now)
        winner: Optional[Verdict] = None
        for rule in self._rules:
            verdict = rule.verdict_for(flag, user_id, instant)
            if verdict is not None and (winner is None or verdict.outranks(winner)):
                winner = verdict
        return winner is not None and winner.enabled

    def __repr__(self) -> str:
        return f"Resolver({list(self._rules)!r})"
