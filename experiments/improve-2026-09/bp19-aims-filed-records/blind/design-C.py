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

Some rules depend on the clock — :class:`ScheduledRollout` ramps a flag across a window — so the
instant is part of the question rather than something a rule reads for itself:
:meth:`Resolver.is_enabled` takes ``now`` (epoch seconds, defaulting to the current time) and hands
the one instant to every rule, which is what lets a test pin the clock and what keeps two rules
from disagreeing about what time it is. A rule with nothing to say about time ignores the argument.
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


def _checked_percent(name: str, value: float) -> float:
    """Return ``value`` if it is a share of the population, else raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100, got {value}")
    return value


def _checked_epoch_seconds(name: str, value: int) -> int:
    """Return ``value`` if it is an instant in integer epoch seconds, else raise."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be integer epoch seconds, got {type(value).__name__}")
    return value


def _moment(now: Optional[float]) -> float:
    """Resolve the instant a question is asked about; ``None`` means the current time."""
    if now is None:
        return int(time.time())
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
    """A statement about one flag. Rules are immutable and free of state between calls."""

    @abstractmethod
    def verdict_for(self, flag: str, user_id: str, now: float) -> Optional[Verdict]:
        """Return this rule's verdict at ``now``, or ``None`` if the rule does not apply.

        ``now`` is epoch seconds, supplied by the caller rather than read from the clock, so a
        rule stays a pure function of its arguments. Rules that do not depend on time ignore it.
        """


class _FlagRule(Rule):
    """A rule scoped to a single flag; it abstains on every other flag."""

    def __init__(self, flag: str) -> None:
        if not isinstance(flag, str):
            raise TypeError(f"flag must be a string, got {type(flag).__name__}")
        self._flag = flag

    @property
    def flag(self) -> str:
        return self._flag

    def verdict_for(self, flag: str, user_id: str, now: float) -> Optional[Verdict]:
        if flag != self._flag:
            return None
        return self._verdict_for_own_flag(user_id, now)

    @abstractmethod
    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        """Return the verdict for a user of this rule's own flag, or ``None``."""


class _RolloutRule(_FlagRule):
    """A rule that hands a flag to a share of the population, picked by a stable bucket.

    A user's bucket is derived from the flag and the user id alone —
    ``int.from_bytes(sha256(f"{flag}:{user_id}")[:8], "big") % 10_000`` — and the flag is on when
    that bucket is below the share of the bucket space. That derivation is part of the contract,
    not an implementation detail: it is what makes the same user get the same answer in another
    process, on another machine, and after a restart, and it is why the built-in ``hash()`` (salted
    per process) cannot be used. It lives here, once, so that every rollout rule — whatever decides
    its share and whenever it decides it — picks the same users for the same share, and so that
    widening a share only ever adds users.
    """

    def _verdict_for_share(self, user_id: str, percent: float) -> Verdict:
        on = self._bucket_of(user_id) < percent * (_BUCKETS / 100)
        return Verdict(enabled=on, authority=Authority.ROLLOUT)

    def _bucket_of(self, user_id: str) -> int:
        digest = hashlib.sha256(f"{self._flag}:{user_id}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % _BUCKETS


class Percentage(_RolloutRule):
    """Turn a flag on for a fixed ``percent`` of users, stably."""

    def __init__(self, flag: str, percent: float) -> None:
        super().__init__(flag)
        self._percent = _checked_percent("percent", percent)

    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        return self._verdict_for_share(user_id, self._percent)

    def __repr__(self) -> str:
        return f"Percentage({self.flag!r}, {self._percent!r})"


class ScheduledRollout(_RolloutRule):
    """Ramp a flag from ``start_percent`` to ``end_percent`` across ``[start_at, end_at)``.

    Outside the window the ramp holds still: before ``start_at`` the share is ``start_percent``,
    at or after ``end_at`` it is ``end_percent``, so a schedule that has run its course keeps
    answering without anyone having to replace it. ``start_at`` and ``end_at`` are integer epoch
    seconds and the window may be empty (``end_at == start_at``), which makes the ramp a step.

    The share moves with the clock but the bucket does not, so at any one instant the answer is
    still a pure function of the flag and the user id — the same user gets the same answer for the
    same flag at the same instant, in any process. A ramp that only rises therefore only ever adds
    users, and one that only falls only ever removes them; ``end_percent`` below ``start_percent``
    is a deliberate ramp-down, not an error.
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
        self._start_percent = _checked_percent("start_percent", start_percent)
        self._end_percent = _checked_percent("end_percent", end_percent)
        self._start_at = _checked_epoch_seconds("start_at", start_at)
        self._end_at = _checked_epoch_seconds("end_at", end_at)
        if self._end_at < self._start_at:
            raise ValueError(
                f"end_at must not be before start_at, got {end_at} before {start_at}"
            )

    def percent_at(self, now: float) -> float:
        """The share of users the flag is on for at ``now``, interpolated across the window."""
        # The end is checked first so that an empty window reads as finished rather than
        # not-yet-started, and so that the window below is never of zero length.
        if now >= self._end_at:
            return self._end_percent
        if now <= self._start_at:
            return self._start_percent
        travelled = (now - self._start_at) / (self._end_at - self._start_at)
        return self._start_percent + (self._end_percent - self._start_percent) * travelled

    def _verdict_for_own_flag(self, user_id: str, now: float) -> Optional[Verdict]:
        return self._verdict_for_share(user_id, self.percent_at(now))

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

    The rules are captured at construction; the answer for a given pair at a given instant never
    changes afterwards, and it does not depend on the order the rules were given in.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules = tuple(rules)
        for rule in self._rules:
            if not isinstance(rule, Rule):
                raise TypeError(f"not a rule: {rule!r}")

    def is_enabled(self, flag: str, user_id: str, now: Optional[float] = None) -> bool:
        """Whether ``flag`` is on for ``user_id`` at ``now``.

        The strongest verdict among the rules that apply decides it. A flag no rule speaks about
        is off. ``now`` is epoch seconds and defaults to the current time; it is resolved once and
        shared by every rule, so a question asked of a schedule answers about a single instant and
        a test can pin that instant.
        """
        moment = _moment(now)
        winner: Optional[Verdict] = None
        for rule in self._rules:
            verdict = rule.verdict_for(flag, user_id, moment)
            if verdict is not None and (winner is None or verdict.outranks(winner)):
                winner = verdict
        return winner is not None and winner.enabled

    def __repr__(self) -> str:
        return f"Resolver({list(self._rules)!r})"
