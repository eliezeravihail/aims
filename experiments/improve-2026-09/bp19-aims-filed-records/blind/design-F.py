"""Feature-flag resolution: decide whether a flag is on for a given user.

A :class:`Resolver` holds rules. Asked about a (flag, user) pair at an instant, every rule either
abstains or returns a :class:`Verdict` — an answer plus the authority it carries. The strongest
verdict wins; if no rule answers, the feature is off.

    >>> resolver = Resolver([Percentage("search", 50), BlockList("search", ["u7"])])
    >>> resolver.is_enabled("search", "u7")
    False

The ordering of verdicts is a published product rule and lives in exactly one place
(:meth:`Verdict.outranks`): an explicit list outranks a percentage rollout, and within the same
authority "off" outranks "on" — which is what makes a block beat an allow. A new kind of rule
declares the authority it speaks with and needs no change to :class:`Resolver`.

Time enters only as the instant a question is asked about: :meth:`Resolver.is_enabled` takes an
optional ``now`` (integer epoch seconds, defaulting to the current time), stamps it once, and hands
that same instant to every rule. Rules stay pure functions of (flag, user, instant), so a caller can
pin ``now`` and get a reproducible answer.
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


def _bucket_of(flag: str, user_id: str) -> int:
    """The user's bucket for this flag — the published rollout contract, in one place.

    ``int.from_bytes(sha256(f"{flag}:{user_id}").digest()[:8], "big") % 10_000``. Every rollout rule
    buckets this way, so a user keeps their place as a rollout widens, ramps, or is replaced by a
    fixed percentage. It is what makes the same user get the same answer in another process, on
    another machine, and after a restart, and it is why the built-in ``hash()`` (salted per process)
    cannot be used. Changing it would move live users between cohorts.
    """
    digest = hashlib.sha256(f"{flag}:{user_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % _BUCKETS


def _validated_percent(value: float, name: str) -> float:
    """Return ``value`` if it is a real number in 0–100, else raise at the caller's construction."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100, got {value}")
    return value


def _validated_instant(value: int, name: str) -> int:
    """Return ``value`` if it is an integer epoch-seconds time, else raise.

    Times are integer seconds by contract, so a float is refused rather than silently truncated;
    ``bool`` is refused for the same reason ``percent`` refuses it.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer epoch-seconds time, got {type(value).__name__}")
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
    """A statement about one flag.

    Rules are immutable and free of state between calls; the instant a question is asked about is
    handed in, never read from the clock, so the same arguments always give the same verdict.
    """

    @abstractmethod
    def verdict_for(self, flag: str, user_id: str, now: int) -> Optional[Verdict]:
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

    def verdict_for(self, flag: str, user_id: str, now: int) -> Optional[Verdict]:
        if flag != self._flag:
            return None
        return self._verdict_for_own_flag(user_id, now)

    @abstractmethod
    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
        """Return the verdict for a user of this rule's own flag, or ``None``."""


class _RolloutRule(_FlagRule):
    """Turn a flag on for the share of users whose bucket falls below a percentage.

    Subclasses say only what the percentage is at a given instant; the bucketing, the comparison,
    and the authority are the same for every rollout, which is what lets a user keep their place
    when a fixed rollout is replaced by a ramp, or a ramp by a fixed rollout.
    """

    def _verdict_for_own_flag(self, user_id: str, now: int) -> Optional[Verdict]:
        on = _bucket_of(self._flag, user_id) < self._percent_at(now) * (_BUCKETS / 100)
        return Verdict(enabled=on, authority=Authority.ROLLOUT)

    @abstractmethod
    def _percent_at(self, now: int) -> float:
        """The share of users this rule turns the flag on for at ``now``."""


class Percentage(_RolloutRule):
    """Turn a flag on for ``percent`` of users, stably.

    A user's bucket is derived from the flag and the user id alone (see :func:`_bucket_of`), and the
    flag is on when that bucket is below ``percent`` of the bucket space. That derivation is part of
    the contract, not an implementation detail. Widening ``percent`` only ever adds users.
    """

    def __init__(self, flag: str, percent: float) -> None:
        super().__init__(flag)
        self._percent = _validated_percent(percent, "percent")

    def _percent_at(self, now: int) -> float:
        return self._percent

    def __repr__(self) -> str:
        return f"Percentage({self.flag!r}, {self._percent!r})"


class ScheduledRollout(_RolloutRule):
    """Ramp a flag from ``start_percent`` to ``end_percent`` across ``[start_at, end_at)``.

    Times are integer epoch seconds. Before ``start_at`` the rule behaves exactly as
    ``Percentage(flag, start_percent)``; at or after ``end_at`` exactly as
    ``Percentage(flag, end_percent)``; in between the percentage moves linearly with the clock. An
    empty window (``start_at == end_at``) is therefore a step from one percentage to the other.

    Users are bucketed by the same published derivation every rollout uses, so at any instant the
    answer is a pure function of (flag, user, instant): a user picked up by a rising ramp keeps the
    feature for the rest of the ramp, and swapping a finished ramp for the equivalent
    :class:`Percentage` moves nobody. ``end_percent`` below ``start_percent`` is allowed and ramps
    back down, which does take the feature away from users as it narrows.
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
        self._start_at = _validated_instant(start_at, "start_at")
        self._end_at = _validated_instant(end_at, "end_at")
        if self._end_at < self._start_at:
            raise ValueError(
                f"end_at must not be before start_at, got {end_at} < {start_at}"
            )

    def _percent_at(self, now: int) -> float:
        if now < self._start_at:
            return self._start_percent
        if now >= self._end_at:
            return self._end_percent
        # start_at <= now < end_at, so the window is non-empty and the division is safe.
        elapsed = (now - self._start_at) / (self._end_at - self._start_at)
        return self._start_percent + (self._end_percent - self._start_percent) * elapsed

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

    The rules are captured at construction; the answer for a given pair at a given instant never
    changes afterwards, and it does not depend on the order the rules were given in.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules = tuple(rules)
        for rule in self._rules:
            if not isinstance(rule, Rule):
                raise TypeError(f"not a rule: {rule!r}")

    def is_enabled(self, flag: str, user_id: str, now: Optional[int] = None) -> bool:
        """Whether ``flag`` is on for ``user_id`` at ``now``.

        ``now`` is integer epoch seconds and defaults to the current time. It is stamped once here
        and handed to every rule, so a single call is answered as of one instant however long it
        takes, and a test can pin the clock by passing it.

        The strongest verdict among the rules that apply decides it. A flag no rule speaks about
        is off.
        """
        instant = int(time.time()) if now is None else _validated_instant(now, "now")
        winner: Optional[Verdict] = None
        for rule in self._rules:
            verdict = rule.verdict_for(flag, user_id, instant)
            if verdict is not None and (winner is None or verdict.outranks(winner)):
                winner = verdict
        return winner is not None and winner.enabled

    def __repr__(self) -> str:
        return f"Resolver({list(self._rules)!r})"
