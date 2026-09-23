"""Tests for flags.py — one test per non-trivial decision in the resolution rule."""

import hashlib
import itertools
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

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


class ScheduledRamp(unittest.TestCase):
    # An arbitrary window of 1_000 seconds, so "before", "inside" and "after" are easy to name.
    START, END = 1_700_000_000, 1_700_001_000

    def _ramp(self, start_percent=0, end_percent=100):
        return Resolver(
            [ScheduledRollout("search", start_percent, end_percent, self.START, self.END)]
        )

    def _count_on(self, resolver, now, count=2_000):
        return sum(resolver.is_enabled("search", f"user-{i}", now=now) for i in range(count))

    def test_before_the_window_it_is_the_start_percentage(self):
        resolver = self._ramp(0, 100)
        self.assertEqual(self._count_on(resolver, self.START - 1), 0)
        self.assertEqual(self._count_on(resolver, 0), 0)

    def test_the_window_is_half_open_so_it_opens_at_the_start_percentage(self):
        self.assertEqual(self._count_on(self._ramp(0, 100), self.START), 0)

    def test_from_end_at_on_it_is_the_end_percentage(self):
        resolver = self._ramp(0, 100)
        self.assertEqual(self._count_on(resolver, self.END), 2_000)
        self.assertEqual(self._count_on(resolver, self.END + 10_000_000), 2_000)

    def test_the_middle_of_the_window_is_the_middle_of_the_ramp(self):
        on = self._count_on(self._ramp(0, 100), self.START + 500)
        self.assertLess(abs(on - 1_000), 100, on)

    def test_the_ramp_is_linear_across_the_window(self):
        resolver = self._ramp(0, 100)
        for tenths in range(1, 10):
            now = self.START + 100 * tenths
            on = self._count_on(resolver, now, 5_000)
            self.assertLess(abs(on - 500 * tenths), 200, (tenths, on))

    def test_a_ramp_hands_out_the_same_cohort_as_a_fixed_percentage_of_that_size(self):
        # The ramp reads the same buckets, so where it stands at 25% it has exactly the users a
        # Percentage(25) has — a flag can be moved from one rule to the other without churn.
        ramp = self._ramp(0, 100)
        fixed = Resolver([Percentage("search", 25)])
        a_quarter_in = self.START + 250
        for i in range(500):
            user_id = f"user-{i}"
            self.assertEqual(
                ramp.is_enabled("search", user_id, now=a_quarter_in),
                fixed.is_enabled("search", user_id),
                user_id,
            )

    def test_a_rising_ramp_only_ever_adds_users(self):
        # Monotonicity over time: the guarantee widening a Percentage gives, now across a window.
        resolver = self._ramp(10, 90)
        for i in range(500):
            user_id = f"user-{i}"
            was_on = False
            for now in range(self.START - 50, self.END + 50, 25):
                on = resolver.is_enabled("search", user_id, now=now)
                self.assertFalse(was_on and not on, (user_id, now))
                was_on = was_on or on

    def test_a_falling_ramp_only_ever_removes_users(self):
        resolver = self._ramp(100, 0)
        for i in range(500):
            user_id = f"user-{i}"
            was_off = False
            for now in range(self.START - 50, self.END + 50, 25):
                on = resolver.is_enabled("search", user_id, now=now)
                self.assertFalse(was_off and on, (user_id, now))
                was_off = was_off or not on

    def test_the_same_instant_always_gives_the_same_answer(self):
        resolver = self._ramp(0, 100)
        mid = self.START + 333
        first = [resolver.is_enabled("search", f"u{i}", now=mid) for i in range(200)]
        second = [resolver.is_enabled("search", f"u{i}", now=mid) for i in range(200)]
        self.assertEqual(first, second)

    def test_an_empty_window_is_a_clean_step(self):
        resolver = Resolver([ScheduledRollout("search", 0, 100, self.START, self.START)])
        self.assertFalse(resolver.is_enabled("search", "u1", now=self.START - 1))
        self.assertTrue(resolver.is_enabled("search", "u1", now=self.START))

    def test_a_flat_ramp_is_just_a_percentage(self):
        flat = Resolver([ScheduledRollout("search", 40, 40, self.START, self.END)])
        fixed = Resolver([Percentage("search", 40)])
        for i in range(300):
            user_id = f"user-{i}"
            self.assertEqual(
                flat.is_enabled("search", user_id, now=self.START + 500),
                fixed.is_enabled("search", user_id),
                user_id,
            )

    def test_a_ramp_does_not_speak_about_other_flags(self):
        resolver = self._ramp(0, 100)
        self.assertFalse(resolver.is_enabled("billing", "u1", now=self.END))

    def test_a_ramp_speaks_with_rollout_authority_so_the_lists_still_win(self):
        blocked = Resolver(
            [
                ScheduledRollout("search", 100, 100, self.START, self.END),
                BlockList("search", ["u1"]),
            ]
        )
        self.assertFalse(blocked.is_enabled("search", "u1", now=self.END))
        self.assertTrue(blocked.is_enabled("search", "u2", now=self.END))

        allowed = Resolver(
            [
                ScheduledRollout("search", 0, 0, self.START, self.END),
                AllowList("search", ["u1"]),
            ]
        )
        self.assertTrue(allowed.is_enabled("search", "u1", now=self.END))
        self.assertFalse(allowed.is_enabled("search", "u2", now=self.END))

    def test_two_ramps_on_one_flag_resolve_restrictively(self):
        # Same authority, so "off" wins, exactly as it does for two Percentage rules. Mirrored
        # ramps disagree at every instant in the window, and both are asked about that one
        # instant, so the answer is the intersection of the two cohorts.
        rising = ScheduledRollout("search", 0, 100, self.START, self.END)
        falling = ScheduledRollout("search", 100, 0, self.START, self.END)
        both = Resolver([rising, falling])
        for now in range(self.START, self.END, 100):
            for i in range(50):
                user_id = f"user-{i}"
                in_both = Resolver([rising]).is_enabled(
                    "search", user_id, now=now
                ) and Resolver([falling]).is_enabled("search", user_id, now=now)
                self.assertEqual(
                    both.is_enabled("search", user_id, now=now), in_both, (user_id, now)
                )


class NowDefaultsToTheClock(unittest.TestCase):
    def test_a_window_already_past_resolves_to_the_end_percentage(self):
        resolver = Resolver([ScheduledRollout("search", 0, 100, 1_000_000, 1_000_001)])
        self.assertTrue(resolver.is_enabled("search", "u1"))

    def test_the_clock_is_read_where_an_explicit_now_would_have_gone(self):
        resolver = Resolver([ScheduledRollout("search", 0, 100, 1_700_000_000, 1_700_001_000)])
        mid_window = 1_700_000_400
        with mock.patch("flags.time.time", return_value=mid_window + 0.75):
            from_the_clock = [resolver.is_enabled("search", f"u{i}") for i in range(200)]
        explicit = [resolver.is_enabled("search", f"u{i}", now=mid_window) for i in range(200)]
        self.assertEqual(from_the_clock, explicit)

    def test_a_window_still_ahead_resolves_to_the_start_percentage(self):
        far_off = 4_000_000_000
        resolver = Resolver([ScheduledRollout("search", 0, 100, far_off, far_off + 1)])
        self.assertFalse(resolver.is_enabled("search", "u1"))

    def test_timeless_rules_give_the_same_answer_at_every_instant(self):
        resolver = Resolver([BlockList("search", ["u1"]), Percentage("search", 100)])
        self.assertFalse(resolver.is_enabled("search", "u1"))
        self.assertTrue(resolver.is_enabled("search", "u2"))
        for now in (0, 1_700_000_000, 4_000_000_000):
            self.assertFalse(resolver.is_enabled("search", "u1", now=now), now)
            self.assertTrue(resolver.is_enabled("search", "u2", now=now), now)


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

    def test_both_ramp_percentages_are_range_checked_at_construction(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", -1, 100, 0, 10)
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 101, 0, 10)

    def test_non_integer_window_times_are_rejected(self):
        for start_at, end_at in ((0.5, 10), (0, 10.5), ("0", 10), (True, 10)):
            with self.assertRaises(TypeError, msg=(start_at, end_at)):
                ScheduledRollout("search", 0, 100, start_at, end_at)

    def test_a_window_that_ends_before_it_starts_is_rejected(self):
        with self.assertRaises(ValueError):
            ScheduledRollout("search", 0, 100, 10, 9)

    def test_an_empty_window_is_accepted(self):
        ScheduledRollout("search", 0, 100, 10, 10)

    def test_a_ramp_down_is_accepted(self):
        ScheduledRollout("search", 100, 0, 0, 10)

    def test_a_non_integer_now_is_rejected(self):
        resolver = Resolver([Percentage("search", 100)])
        for now in (1.5, "1700000000", True):
            with self.assertRaises(TypeError, msg=now):
                resolver.is_enabled("search", "u1", now=now)


if __name__ == "__main__":
    unittest.main()
