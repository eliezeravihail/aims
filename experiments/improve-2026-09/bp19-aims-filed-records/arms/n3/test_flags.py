"""Tests for flags.py — one test per non-trivial decision in the resolution rule."""

import hashlib
import itertools
import subprocess
import sys
import unittest
from pathlib import Path

from flags import AllowList, BlockList, Percentage, Resolver, ScheduledRollout


class DefaultOff(unittest.TestCase):
    def test_no_rules_at_all_is_off(self):
        self.assertFalse(Resolver([]).is_enabled("search", "u1"))

    def test_no_rule_for_this_flag_is_off(self):
        resolver = Resolver([AllowList("other", ["u1"]), Percentage("other", 100)])
        self.assertFalse(resolver.is_enabled("search", "u1"))

    def test_rules_for_other_flags_do_not_leak(self):
        resolver = Resolver([BlockList("other", ["u1"]), Percentage("search", 100)])
        self.assertTrue(resolver.is_enabled("search", "u1"))


class ExplicitLists(unittest.TestCase):
    def test_allow_list_enables_listed_user_only(self):
        resolver = Resolver([AllowList("search", ["u1", "u2"])])
        self.assertTrue(resolver.is_enabled("search", "u1"))
        self.assertTrue(resolver.is_enabled("search", "u2"))
        self.assertFalse(resolver.is_enabled("search", "u3"))

    def test_block_list_alone_disables_listed_user_and_others_stay_off(self):
        resolver = Resolver([BlockList("search", ["u1"])])
        self.assertFalse(resolver.is_enabled("search", "u1"))
        self.assertFalse(resolver.is_enabled("search", "u9"))

    def test_empty_list_matches_nobody(self):
        self.assertFalse(Resolver([AllowList("search", [])]).is_enabled("search", "u1"))

    def test_duplicate_ids_are_harmless(self):
        resolver = Resolver([AllowList("search", ["u1", "u1"])])
        self.assertTrue(resolver.is_enabled("search", "u1"))

    def test_user_ids_are_copied_so_later_mutation_cannot_change_answers(self):
        ids = ["u1"]
        resolver = Resolver([AllowList("search", ids)])
        ids.append("u2")
        self.assertFalse(resolver.is_enabled("search", "u2"))


class Precedence(unittest.TestCase):
    def test_block_beats_allow(self):
        resolver = Resolver([AllowList("search", ["u1"]), BlockList("search", ["u1"])])
        self.assertFalse(resolver.is_enabled("search", "u1"))

    def test_block_beats_a_hundred_percent_rollout(self):
        resolver = Resolver([Percentage("search", 100), BlockList("search", ["u1"])])
        self.assertFalse(resolver.is_enabled("search", "u1"))
        self.assertTrue(resolver.is_enabled("search", "u2"))

    def test_allow_beats_a_zero_percent_rollout(self):
        resolver = Resolver([Percentage("search", 0), AllowList("search", ["u1"])])
        self.assertTrue(resolver.is_enabled("search", "u1"))
        self.assertFalse(resolver.is_enabled("search", "u2"))

    def test_answer_is_independent_of_rule_order(self):
        rules = [
            Percentage("search", 100),
            AllowList("search", ["u1", "u2"]),
            BlockList("search", ["u1"]),
        ]
        for ordering in itertools.permutations(rules):
            resolver = Resolver(list(ordering))
            self.assertFalse(resolver.is_enabled("search", "u1"), ordering)
            self.assertTrue(resolver.is_enabled("search", "u2"), ordering)

    def test_off_wins_within_a_tier_so_two_percentage_rules_are_deterministic(self):
        rules = [Percentage("search", 100), Percentage("search", 0)]
        self.assertFalse(Resolver(rules).is_enabled("search", "u1"))
        self.assertFalse(Resolver(rules[::-1]).is_enabled("search", "u1"))


class PercentageBuckets(unittest.TestCase):
    def test_zero_percent_is_on_for_nobody(self):
        resolver = Resolver([Percentage("search", 0)])
        self.assertFalse(any(resolver.is_enabled("search", f"u{i}") for i in range(500)))

    def test_hundred_percent_is_on_for_everybody(self):
        resolver = Resolver([Percentage("search", 100)])
        self.assertTrue(all(resolver.is_enabled("search", f"u{i}") for i in range(500)))

    def test_bucket_follows_the_published_contract(self):
        # Recomputed here from the documented contract, not read back from the module.
        resolver = Resolver([Percentage("search", 25)])
        for i in range(200):
            user_id = f"u{i}"
            digest = hashlib.sha256(f"search:{user_id}".encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:8], "big") % 10_000
            self.assertEqual(resolver.is_enabled("search", user_id), bucket < 2_500, user_id)

    def test_two_flags_do_not_select_the_same_users(self):
        # The bucket is per (flag, user), so a 50% rollout of one flag must not hand the feature
        # to exactly the same people as a 50% rollout of another.
        users = [f"user-{i}" for i in range(500)]
        search = {u for u in users if Resolver([Percentage("search", 50)]).is_enabled("search", u)}
        billing = {u for u in users if Resolver([Percentage("billing", 50)]).is_enabled("billing", u)}
        self.assertLess(len(search & billing), 0.8 * len(search))

    def test_distribution_is_close_to_the_requested_percentage(self):
        resolver = Resolver([Percentage("search", 30)])
        on = sum(resolver.is_enabled("search", f"user-{i}") for i in range(10_000))
        self.assertLess(abs(on - 3_000), 200, on)

    def test_a_fractional_percentage_is_honoured(self):
        resolver = Resolver([Percentage("search", 0.5)])
        on = sum(resolver.is_enabled("search", f"user-{i}") for i in range(20_000))
        self.assertLess(abs(on - 100), 60, on)

    def test_raising_the_percentage_only_adds_users(self):
        # Monotonicity: nobody who had the feature loses it when the rollout widens.
        small = Resolver([Percentage("search", 10)])
        large = Resolver([Percentage("search", 40)])
        for i in range(2_000):
            user_id = f"user-{i}"
            if small.is_enabled("search", user_id):
                self.assertTrue(large.is_enabled("search", user_id), user_id)


class StableAcrossProcesses(unittest.TestCase):
    def _answers_from_a_fresh_process(self, hash_seed):
        script = (
            "from flags import Percentage, Resolver;"
            "r = Resolver([Percentage('search', 50)]);"
            "print(''.join('1' if r.is_enabled('search', f'u{i}') else '0' for i in range(64)))"
        )
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(Path(__file__).resolve().parent),
            env={"PYTHONHASHSEED": hash_seed, "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def test_answers_survive_a_restart_with_a_different_hash_seed(self):
        first = self._answers_from_a_fresh_process("0")
        second = self._answers_from_a_fresh_process("12345")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_golden_vector_pins_the_bucketing_for_existing_users(self):
        # Changing the bucketing would silently move live users; this vector makes that visible.
        resolver = Resolver([Percentage("search", 50)])
        answers = "".join(
            "1" if resolver.is_enabled("search", f"u{i}") else "0" for i in range(16)
        )
        self.assertEqual(answers, "1011100001100011")


class Validation(unittest.TestCase):
    def test_percent_below_zero_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            Percentage("search", -1)

    def test_percent_above_hundred_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            Percentage("search", 101)

    def test_percent_boundaries_are_accepted(self):
        Percentage("search", 0)
        Percentage("search", 100)

    def test_non_numeric_percent_is_rejected(self):
        with self.assertRaises(TypeError):
            Percentage("search", "50")

    def test_boolean_percent_is_rejected(self):
        with self.assertRaises(TypeError):
            Percentage("search", True)

    def test_a_non_rule_in_the_rule_list_is_rejected_at_construction(self):
        with self.assertRaises(TypeError):
            Resolver(["search"])

    def test_a_bare_string_of_user_ids_is_rejected(self):
        with self.assertRaises(TypeError):
            AllowList("search", "u1")


#: A fixed ramp window, so every scheduled test says something definite about a known instant.
_START = 1_700_000_000
_END = _START + 1_000
_USERS = [f"user-{i}" for i in range(2_000)]


def _live_users(resolver, now):
    return {u for u in _USERS if resolver.is_enabled("search", u, now)}


class ScheduledRamp(unittest.TestCase):
    def test_before_the_window_it_is_exactly_the_starting_percentage(self):
        ramp = Resolver([ScheduledRollout("search", 10, 90, _START, _END)])
        flat = Resolver([Percentage("search", 10)])
        for now in (0, _START - 86_400, _START - 1):
            self.assertEqual(_live_users(ramp, now), _live_users(flat, 0), now)

    def test_at_the_start_instant_it_is_still_the_starting_percentage(self):
        ramp = Resolver([ScheduledRollout("search", 10, 90, _START, _END)])
        flat = Resolver([Percentage("search", 10)])
        self.assertEqual(_live_users(ramp, _START), _live_users(flat, 0))

    def test_from_the_end_instant_on_it_is_exactly_the_ending_percentage(self):
        # The window is half-open, so end_at itself already belongs to the finished rollout.
        ramp = Resolver([ScheduledRollout("search", 10, 90, _START, _END)])
        flat = Resolver([Percentage("search", 90)])
        for now in (_END, _END + 1, _END + 10_000_000):
            self.assertEqual(_live_users(ramp, now), _live_users(flat, 0), now)

    def test_halfway_through_the_window_it_is_the_halfway_percentage(self):
        ramp = Resolver([ScheduledRollout("search", 0, 100, _START, _END)])
        flat = Resolver([Percentage("search", 50)])
        self.assertEqual(_live_users(ramp, _START + 500), _live_users(flat, 0))

    def test_the_ramp_only_ever_adds_users_as_time_passes(self):
        # The point of reusing the bucket: a user reached mid-ramp is not dropped later.
        resolver = Resolver([ScheduledRollout("search", 5, 95, _START, _END)])
        live = set()
        for offset in range(-1, 1_002, 50):
            now_live = _live_users(resolver, _START + offset)
            self.assertTrue(live <= now_live, offset)
            live = now_live

    def test_the_same_instant_always_gives_the_same_answer(self):
        resolver = Resolver([ScheduledRollout("search", 0, 100, _START, _END)])
        for user_id in ("u1", "u2", "u3"):
            answers = {resolver.is_enabled("search", user_id, _START + 337) for _ in range(5)}
            self.assertEqual(len(answers), 1, user_id)

    def test_a_ramp_can_run_downwards(self):
        resolver = Resolver([ScheduledRollout("search", 100, 0, _START, _END)])
        self.assertEqual(len(_live_users(resolver, _START)), len(_USERS))
        self.assertEqual(_live_users(resolver, _END), set())
        self.assertTrue(_live_users(resolver, _START + 500) <= _live_users(resolver, _START + 250))

    def test_an_empty_window_is_a_clean_switch(self):
        resolver = Resolver([ScheduledRollout("search", 0, 100, _START, _START)])
        self.assertFalse(resolver.is_enabled("search", "u1", _START - 1))
        self.assertTrue(resolver.is_enabled("search", "u1", _START))

    def test_percent_at_reports_the_live_percentage(self):
        rule = ScheduledRollout("search", 20, 60, _START, _END)
        self.assertEqual(rule.percent_at(_START - 1), 20)
        self.assertEqual(rule.percent_at(_START), 20)
        self.assertEqual(rule.percent_at(_START + 250), 30)
        self.assertEqual(rule.percent_at(_START + 500), 40)
        self.assertEqual(rule.percent_at(_END), 60)
        self.assertEqual(rule.percent_at(_END + 10_000), 60)

    def test_a_finished_ramp_needs_no_clock_from_the_caller(self):
        past = Resolver([ScheduledRollout("search", 0, 100, _START, _END)])
        self.assertTrue(past.is_enabled("search", "u1"))

    def test_an_unstarted_ramp_needs_no_clock_from_the_caller(self):
        future = Resolver([ScheduledRollout("search", 0, 100, 4_000_000_000, 4_000_001_000)])
        self.assertFalse(future.is_enabled("search", "u1"))


class ScheduledPrecedence(unittest.TestCase):
    def test_a_block_beats_a_finished_ramp(self):
        resolver = Resolver(
            [ScheduledRollout("search", 0, 100, _START, _END), BlockList("search", ["u1"])]
        )
        self.assertFalse(resolver.is_enabled("search", "u1", _END))
        self.assertTrue(resolver.is_enabled("search", "u2", _END))

    def test_an_allow_beats_an_unstarted_ramp(self):
        resolver = Resolver(
            [ScheduledRollout("search", 0, 100, _START, _END), AllowList("search", ["u1"])]
        )
        self.assertTrue(resolver.is_enabled("search", "u1", _START - 1))
        self.assertFalse(resolver.is_enabled("search", "u2", _START - 1))

    def test_a_ramp_ties_with_a_percentage_as_a_rollout_so_off_still_wins(self):
        rules = [Percentage("search", 100), ScheduledRollout("search", 0, 0, _START, _END)]
        self.assertFalse(Resolver(rules).is_enabled("search", "u1", _END))
        self.assertFalse(Resolver(rules[::-1]).is_enabled("search", "u1", _END))

    def test_a_ramp_for_another_flag_does_not_leak(self):
        resolver = Resolver([ScheduledRollout("other", 0, 100, _START, _END)])
        self.assertFalse(resolver.is_enabled("search", "u1", _END))


class ScheduledValidation(unittest.TestCase):
    def test_an_end_before_the_start_is_rejected(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 100, _END, _START)

    def test_percentages_are_validated_like_a_plain_rollout(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", -1, 100, _START, _END)
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 101, _START, _END)
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, "100", _START, _END)

    def test_non_integer_times_are_rejected(self):
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, float(_START), _END)
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, _START, str(_END))
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, True, _END)

    def test_a_non_numeric_now_is_rejected(self):
        resolver = Resolver([Percentage("search", 100)])
        with self.assertRaises(TypeError):
            resolver.is_enabled("search", "u1", "2026-01-01")


class ClockPlumbing(unittest.TestCase):
    def test_timeless_rules_ignore_the_clock(self):
        resolver = Resolver([Percentage("search", 50), BlockList("search", ["u1"])])
        for now in (None, 0, _START, _END + 10**9):
            self.assertFalse(resolver.is_enabled("search", "u1", now), now)
            self.assertEqual(
                resolver.is_enabled("search", "u2", now),
                resolver.is_enabled("search", "u2"),
                now,
            )

    def test_every_rule_in_one_answer_sees_the_same_instant(self):
        # Two ramps that cross: at the crossing instant one is fully on and the other fully off,
        # and "off" wins. A second clock reading anywhere in the resolver could not produce that.
        rules = [
            ScheduledRollout("search", 0, 100, _START, _END),
            ScheduledRollout("search", 100, 0, _START, _END),
        ]
        self.assertFalse(Resolver(rules).is_enabled("search", "u1", _END))
        self.assertFalse(Resolver(rules[::-1]).is_enabled("search", "u1", _END))

    def test_a_rule_can_still_be_asked_directly_without_a_clock(self):
        self.assertIsNone(Percentage("other", 100).verdict_for("search", "u1"))
        self.assertTrue(Percentage("search", 100).verdict_for("search", "u1").enabled)


if __name__ == "__main__":
    unittest.main()
