"""Tests for flags.py — one test per non-trivial decision in the resolution rule."""

import hashlib
import itertools
import subprocess
import sys
import time
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

    def test_a_ramp_that_ends_before_it_starts_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 100, 2_000, 1_000)

    def test_an_empty_ramp_window_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 100, 1_000, 1_000)

    def test_ramp_endpoints_are_validated_like_any_percentage(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", -1, 100, 1_000, 2_000)
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 101, 1_000, 2_000)
        with self.assertRaises(TypeError):
            ScheduledRollout("search", "0", 100, 1_000, 2_000)

    def test_non_integer_times_are_rejected_at_construction(self):
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, 1_000.5, 2_000)
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, 1_000, "2000")
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, True, 2_000)

    def test_a_non_integer_now_is_rejected(self):
        with self.assertRaises(TypeError):
            Resolver([]).is_enabled("search", "u1", "now")


class ScheduledRamp(unittest.TestCase):
    START, END = 1_000_000, 1_000_600  # a ten-minute ramp, in epoch seconds
    USERS = [f"user-{i}" for i in range(2_000)]

    def _ramp(self, start_percent=0, end_percent=100):
        return Resolver(
            [ScheduledRollout("search", start_percent, end_percent, self.START, self.END)]
        )

    def _on_at(self, resolver, now):
        return {u for u in self.USERS if resolver.is_enabled("search", u, now)}

    def _fixed(self, percent):
        return self._on_at(Resolver([Percentage("search", percent)]), self.START)

    def test_before_the_window_it_is_the_starting_percentage(self):
        ramp = self._ramp(10, 90)
        self.assertEqual(self._on_at(ramp, self.START - 1), self._fixed(10))
        self.assertEqual(self._on_at(ramp, 0), self._fixed(10))

    def test_at_the_start_instant_it_is_still_the_starting_percentage(self):
        self.assertEqual(self._on_at(self._ramp(10, 90), self.START), self._fixed(10))

    def test_at_the_end_instant_it_is_already_the_ending_percentage(self):
        # The window is half-open: end_at belongs to "after".
        self.assertEqual(self._on_at(self._ramp(10, 90), self.END), self._fixed(90))

    def test_after_the_window_it_stays_the_ending_percentage(self):
        ramp = self._ramp(10, 90)
        self.assertEqual(self._on_at(ramp, self.END + 10_000_000), self._fixed(90))

    def test_halfway_through_it_is_halfway_between_the_percentages(self):
        self.assertEqual(self._on_at(self._ramp(20, 60), self.START + 300), self._fixed(40))

    def test_the_share_grows_linearly_with_the_clock(self):
        ramp = self._ramp(0, 100)
        for elapsed in (0, 60, 150, 300, 450, 599):
            expected = self._fixed(100 * elapsed / 600)
            self.assertEqual(self._on_at(ramp, self.START + elapsed), expected, elapsed)

    def test_nobody_loses_the_feature_as_the_ramp_widens(self):
        ramp = self._ramp(0, 100)
        held = set()
        for now in range(self.START - 60, self.END + 60, 30):
            on = self._on_at(ramp, now)
            self.assertTrue(held <= on, now)
            held = on

    def test_the_same_instant_always_gives_the_same_answer(self):
        rules = ScheduledRollout("search", 0, 100, self.START, self.END)
        now = self.START + 137
        first = [Resolver([rules]).is_enabled("search", u, now) for u in self.USERS]
        second = [
            Resolver([ScheduledRollout("search", 0, 100, self.START, self.END)]).is_enabled(
                "search", u, now
            )
            for u in self.USERS
        ]
        self.assertEqual(first, second)

    def test_a_ramp_selects_the_same_users_as_the_fixed_rollout_it_passes_through(self):
        # Mid-ramp membership is the published bucket, not a second population: a user at 40%
        # of the ramp is exactly a user of a fixed 40% rollout.
        self.assertEqual(self._on_at(self._ramp(0, 100), self.START + 240), self._fixed(40))

    def test_a_descending_ramp_winds_the_feature_back_down(self):
        ramp = self._ramp(100, 0)
        self.assertEqual(self._on_at(ramp, self.START), set(self.USERS))
        self.assertEqual(self._on_at(ramp, self.START + 300), self._fixed(50))
        self.assertEqual(self._on_at(ramp, self.END), set())

    def test_it_does_not_leak_to_other_flags(self):
        resolver = Resolver([ScheduledRollout("search", 100, 100, self.START, self.END)])
        self.assertTrue(resolver.is_enabled("search", "u1", self.START))
        self.assertFalse(resolver.is_enabled("billing", "u1", self.START))

    def test_now_defaults_to_the_current_time(self):
        now = int(time.time())
        past = Resolver([ScheduledRollout("search", 0, 100, now - 7_200, now - 3_600)])
        future = Resolver([ScheduledRollout("search", 0, 100, now + 3_600, now + 7_200)])
        self.assertTrue(past.is_enabled("search", "u1"))
        self.assertFalse(future.is_enabled("search", "u1"))

    def test_clock_independent_rules_ignore_an_explicit_now(self):
        resolver = Resolver([AllowList("search", ["u1"]), Percentage("search", 100)])
        for now in (0, 1_000_000, 2_000_000_000):
            self.assertTrue(resolver.is_enabled("search", "u1", now), now)
            self.assertTrue(resolver.is_enabled("search", "u2", now), now)


class ScheduledRampPrecedence(unittest.TestCase):
    START, END = 1_000_000, 1_000_600

    def test_a_block_beats_a_fully_ramped_rollout(self):
        rules = [
            ScheduledRollout("search", 0, 100, self.START, self.END),
            BlockList("search", ["u1"]),
        ]
        for ordering in itertools.permutations(rules):
            resolver = Resolver(list(ordering))
            self.assertFalse(resolver.is_enabled("search", "u1", self.END), ordering)

    def test_an_allow_beats_a_not_yet_started_ramp(self):
        rules = [
            ScheduledRollout("search", 0, 100, self.START, self.END),
            AllowList("search", ["u1"]),
        ]
        for ordering in itertools.permutations(rules):
            resolver = Resolver(list(ordering))
            self.assertTrue(resolver.is_enabled("search", "u1", self.START - 1), ordering)

    def test_within_the_rollout_tier_the_restrictive_answer_still_wins(self):
        rules = [
            ScheduledRollout("search", 100, 100, self.START, self.END),
            Percentage("search", 0),
        ]
        self.assertFalse(Resolver(rules).is_enabled("search", "u1", self.START))
        self.assertFalse(Resolver(rules[::-1]).is_enabled("search", "u1", self.START))


if __name__ == "__main__":
    unittest.main()
