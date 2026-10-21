from __future__ import annotations

import unittest
from datetime import datetime, timezone

from refresh_schedule import SHANGHAI, compute_refresh_rate


def shanghai_time(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=SHANGHAI)


class RefreshScheduleTests(unittest.TestCase):
    def test_daytime_window_uses_configured_interval(self) -> None:
        for now in (
            shanghai_time(2026, 10, 21, 7, 10),
            shanghai_time(2026, 10, 21, 12, 0),
            shanghai_time(2026, 10, 21, 22, 39),
        ):
            with self.subTest(now=now):
                self.assertEqual(compute_refresh_rate(now, 1800), 1800)

    def test_nighttime_sleeps_until_the_next_local_day_start(self) -> None:
        cases = (
            (shanghai_time(2026, 10, 21, 6, 59), 660),
            (shanghai_time(2026, 10, 21, 7, 9), 60),
            (shanghai_time(2026, 10, 21, 22, 40), 30_600),
            (shanghai_time(2026, 10, 21, 23, 59), 25_860),
            (shanghai_time(2026, 10, 22, 0, 1), 25_740),
        )
        for now, expected_seconds in cases:
            with self.subTest(now=now):
                self.assertEqual(compute_refresh_rate(now, 1800), expected_seconds)

    def test_date_boundaries_use_datetime_arithmetic(self) -> None:
        cases = (
            (shanghai_time(2026, 10, 31, 22, 40), 30_600),
            (shanghai_time(2026, 12, 31, 23, 59), 25_860),
            (shanghai_time(2028, 2, 29, 22, 40), 30_600),
        )
        for now, expected_seconds in cases:
            with self.subTest(now=now):
                self.assertEqual(compute_refresh_rate(now, 1800), expected_seconds)

    def test_another_timezone_is_normalized_to_shanghai(self) -> None:
        utc_now = datetime(2026, 10, 20, 22, 59, tzinfo=timezone.utc)
        self.assertEqual(compute_refresh_rate(utc_now, 1800), 660)

    def test_rejects_naive_time_or_nonpositive_day_interval(self) -> None:
        with self.assertRaises(ValueError):
            compute_refresh_rate(datetime(2026, 10, 21, 12, 0), 1800)
        with self.assertRaises(ValueError):
            compute_refresh_rate(shanghai_time(2026, 10, 21, 12, 0), 0)


if __name__ == "__main__":
    unittest.main()
