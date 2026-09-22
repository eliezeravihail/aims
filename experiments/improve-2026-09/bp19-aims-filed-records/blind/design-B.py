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

Every question is asked about an instant: :meth:`Resolver.is_enabled` takes ``now`` (integer epoch
seconds, defaulting to the current time) and hands it to every rule, so a time-dependent rule such
as :class:`ScheduledRollout` can be asked about a fixed moment instead of the wall clock. The
answer for a (flag, user) pair at a given instant is the same wherever and whenever it is computed.
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


def _validated_percent(percent: float, name: str) -> float:
    """Return ``percent`` if it is a share of the population, else raise."""
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(percent).__name__}")
    if not 0 <= percent <= 100:
        raise ValueError(f"{name} must be between 0 and 100, got {percent}")
    return percent


def _validated_epoch_seconds(value: int, name: str) -> int:
    """Return ``value`` if it is an integer count of epoch seconds, else raise."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{name} must be an integer count of epoch seconds, e.g. int(time.time()), "
            f"got {type(value).__name__}"
        )
    return value


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
    def verdict_for(self, flag: str, user_id: str, now: int) -> Optional[Verdict]:
        """Return this rule's verdict for the pair at ``now``, or ``None`` if it does not apply.

        ``now`` is an integer count of epoch seconds, supplied by the resolver on every call; a
        rule that does not depend on the clock simply ignores it.
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

    def verdict_for(self, flag: str, user_id: str, now: int) -> Optional[Verdict]:
        if flag != self._flag:
            return None
        return self._verdict_for_own_flag(user_id, now)

    @abstractmethod
    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
        """Return the verdict for a user of this rule's own flag, or ``None``."""


class _BucketedRollout(_FlagRule):
    """A rule that turns a flag on for a share of users, picked by a stable bucket.

    A user's bucket is derived from the flag and the user id alone —
    ``int.from_bytes(sha256(f"{flag}:{user_id}")[:8], "big") % 10_000`` — and the flag is on when
    that bucket is below the share being rolled out. That derivation is part of the contract, not
    an implementation detail: it is what makes the same user get the same answer in another
    process, on another machine, and after a restart, and it is why the built-in ``hash()`` (salted
    per process) cannot be used. Every rollout rule reads the same bucket, so a user sits in one
    place in the population however the share is arrived at, and widening the share only ever adds
    users.
    """

    def _verdict_at(self, user_id: str, percent: float) -> Verdict:
        """The verdict when ``percent`` of the population is rolled out."""
        on = self._bucket_of(user_id) < percent * (_BUCKETS / 100)
        return Verdict(enabled=on, authority=Authority.ROLLOUT)

    def _bucket_of(self, user_id: str) -> int:
        digest = hashlib.sha256(f"{self.flag}:{user_id}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % _BUCKETS


class Percentage(_BucketedRollout):
    """Turn a flag on for ``percent`` of users, stably.

    The share is fixed: the answer for a user never changes until someone changes the rule.
    """

    def __init__(self, flag: str, percent: float) -> None:
        super().__init__(flag)
        self._percent = _validated_percent(percent, "percent")

    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
        return self._verdict_at(user_id, self._percent)

    def __repr__(self) -> str:
        return f"Percentage({self.flag!r}, {self._percent!r})"


class ScheduledRollout(_BucketedRollout):
    """Ramp a flag from ``start_percent`` to ``end_percent`` over ``[start_at, end_at)``.

    Before ``start_at`` the rule answers exactly as ``Percentage(flag, start_percent)`` would;
    from ``end_at`` on, exactly as ``Percentage(flag, end_percent)`` would; in between the share
    grows linearly with the clock. Times are integer epoch seconds.

    The share is the only thing the clock moves: it is still compared against the same published
    bucket as :class:`Percentage`, so everyone asking about the same instant gets the same answer
    for a user, and along a widening ramp a user who has the feature keeps it. A descending ramp
    (``end_percent`` below ``start_percent``) is allowed and winds the feature back down the same
    way.
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
        self._start_percent = _validated_percent(start_percent, "start_percent")
        self._end_percent = _validated_percent(end_percent, "end_percent")
        self._start_at = _validated_epoch_seconds(start_at, "start_at")
        self._end_at = _validated_epoch_seconds(end_at, "end_at")
        if self._end_at <= self._start_at:
            raise ValueError(
                "end_at must be after start_at, got "
                f"start_at={self._start_at}, end_at={self._end_at}"
            )

    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
        return self._verdict_at(user_id, self._percent_at(now))

    def _percent_at(self, now: int) -> float:
        """The share rolled out at ``now``: flat outside the window, linear inside it."""
        if now <= self._start_at:
            return self._start_percent
        if now >= self._end_at:
            return self._end_percent
        progress = (now - self._start_at) / (self._end_at - self._start_at)
        return self._start_percent + (self._end_percent - self._start_percent) * progress

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

    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
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

    The rules are captured at construction; for a given pair and a given instant the answer never
    changes afterwards, and it does not depend on the order the rules were given in.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules = tuple(rules)
        for rule in self._rules:
            if not isinstance(rule, Rule):
                raise TypeError(f"not a rule: {rule!r}")

    def is_enabled(self, flag: str, user_id: str, now: Optional[int] = None) -> bool:
        """Whether ``flag`` is on for ``user_id`` at ``now``.

        ``now`` is an integer count of epoch seconds and defaults to the current time. It is
        settled once here and handed to every rule, so one call is answered as of a single
        instant even while the clock moves; pass it explicitly to ask about a fixed moment.

        The strongest verdict among the rules that apply decides it. A flag no rule speaks about
        is off.
        """
        moment = int(time.time()) if now is None else _validated_epoch_seconds(now, "now")
        winner: Optional[Verdict] = None
        for rule in self._rules:
            verdict = rule.verdict_for(flag, user_id, moment)
            if verdict is not None and (winner is None or verdict.outranks(winner)):
                winner = verdict
        return winner is not None and winner.enabled

    def __repr__(self) -> str:
        return f"Resolver({list(self._rules)!r})"
