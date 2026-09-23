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


class ScheduledRollouts(unittest.TestCase):
    # A window in round numbers: the ramp runs for 1000 seconds from t=1000.
    START, END = 1_000, 2_000

    def _ramp(self, start_percent, end_percent):
        return Resolver(
            [ScheduledRollout("search", start_percent, end_percent, self.START, self.END)]
        )

    def _on_count(self, resolver, now, users=2_000):
        return sum(resolver.is_enabled("search", f"user-{i}", now) for i in range(users))

    def test_before_the_window_it_is_the_start_percentage(self):
        ramp = self._ramp(0, 100)
        for now in (0, self.START - 1):
            self.assertFalse(any(ramp.is_enabled("search", f"u{i}", now) for i in range(200)))

    def test_at_or_after_the_end_it_is_the_end_percentage(self):
        ramp = self._ramp(0, 100)
        for now in (self.END, self.END + 10**6):
            self.assertTrue(all(ramp.is_enabled("search", f"u{i}", now) for i in range(200)))

    def test_the_window_is_half_open_so_the_start_is_in_and_the_end_is_out(self):
        # At start_at the ramp has not moved yet; at end_at it is already finished.
        ramp = self._ramp(0, 100)
        self.assertFalse(ramp.is_enabled("search", "u1", self.START))
        self.assertTrue(ramp.is_enabled("search", "u1", self.END))

    def test_it_ramps_linearly_through_the_window(self):
        ramp = self._ramp(0, 100)
        for fraction in (0.25, 0.5, 0.75):
            now = self.START + int(fraction * (self.END - self.START))
            on = self._on_count(ramp, now)
            self.assertLess(abs(on - fraction * 2_000), 120, (fraction, on))

    def test_outside_the_window_it_agrees_exactly_with_the_equivalent_percentage(self):
        ramp = self._ramp(10, 40)
        fixed_start = Resolver([Percentage("search", 10)])
        fixed_end = Resolver([Percentage("search", 40)])
        for i in range(500):
            user_id = f"user-{i}"
            self.assertEqual(
                ramp.is_enabled("search", user_id, self.START - 1),
                fixed_start.is_enabled("search", user_id),
                user_id,
            )
            self.assertEqual(
                ramp.is_enabled("search", user_id, self.END),
                fixed_end.is_enabled("search", user_id),
                user_id,
            )

    def test_a_rising_ramp_only_ever_adds_users(self):
        # Same bucketing as Percentage, so nobody flickers off as the ramp widens.
        ramp = self._ramp(0, 100)
        held = set()
        for now in range(self.START, self.END + 1, 50):
            on = {f"u{i}" for i in range(300) if ramp.is_enabled("search", f"u{i}", now)}
            self.assertTrue(held <= on, now)
            held = on

    def test_a_descending_ramp_only_ever_removes_users(self):
        ramp = self._ramp(100, 0)
        previous = {f"u{i}" for i in range(300)}
        for now in range(self.START, self.END + 1, 50):
            on = {f"u{i}" for i in range(300) if ramp.is_enabled("search", f"u{i}", now)}
            self.assertTrue(on <= previous, now)
            previous = on

    def test_the_same_instant_always_gives_the_same_answer(self):
        ramp = self._ramp(0, 100)
        now = self.START + 371
        answers = {ramp.is_enabled("search", "u1", now) for _ in range(20)}
        self.assertEqual(len(answers), 1)

    def test_an_empty_window_is_a_step_rather_than_a_division_by_zero(self):
        stepped = Resolver([ScheduledRollout("search", 0, 100, self.START, self.START)])
        self.assertFalse(stepped.is_enabled("search", "u1", self.START - 1))
        self.assertTrue(stepped.is_enabled("search", "u1", self.START))

    def test_it_abstains_on_other_flags(self):
        resolver = Resolver([ScheduledRollout("other", 0, 100, self.START, self.END)])
        self.assertFalse(resolver.is_enabled("search", "u1", self.END))

    def test_explicit_lists_still_outrank_a_ramp(self):
        finished = [ScheduledRollout("search", 0, 100, self.START, self.END)]
        self.assertFalse(
            Resolver(finished + [BlockList("search", ["u1"])]).is_enabled("search", "u1", self.END)
        )
        not_started = [ScheduledRollout("search", 0, 100, self.START, self.END)]
        self.assertTrue(
            Resolver(not_started + [AllowList("search", ["u1"])]).is_enabled("search", "u1", 0)
        )


class CurrentTimeDefault(unittest.TestCase):
    def test_now_defaults_to_the_clock(self):
        past = int(time.time()) - 3_600
        self.assertTrue(
            Resolver([ScheduledRollout("search", 0, 100, past, past + 1)]).is_enabled(
                "search", "u1"
            )
        )
        future = int(time.time()) + 3_600
        self.assertFalse(
            Resolver([ScheduledRollout("search", 0, 100, future, future + 1)]).is_enabled(
                "search", "u1"
            )
        )

    def test_timeless_rules_ignore_now(self):
        resolver = Resolver([Percentage("search", 100), BlockList("search", ["u1"])])
        for now in (None, 0, 10**9):
            self.assertTrue(resolver.is_enabled("search", "u2", now))
            self.assertFalse(resolver.is_enabled("search", "u1", now))


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

    def test_ramp_percent_bounds_are_checked_at_construction(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", -1, 50, 0, 10)
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 101, 0, 10)

    def test_a_window_that_ends_before_it_starts_is_rejected(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 100, 10, 9)

    def test_non_integer_window_times_are_rejected(self):
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, 0.5, 10)
        with self.assertRaises(TypeError):
            ScheduledRollout("search", 0, 100, 0, "10")

    def test_a_non_integer_now_is_rejected(self):
        with self.assertRaises(TypeError):
            Resolver([Percentage("search", 100)]).is_enabled("search", "u1", 1.5)


if __name__ == "__main__":
    unittest.main()
