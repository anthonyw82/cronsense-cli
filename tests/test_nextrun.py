import unittest
from datetime import datetime

from cronsense.nextrun import next_run
from cronsense.parser import CronValidationError, parse


class NextRunBasicsTests(unittest.TestCase):
    def test_every_15_minutes_rounds_up_to_next_slot(self):
        cron = parse("*/15 * * * *")
        after = datetime(2024, 1, 1, 10, 7, 30)
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 1, 10, 15))

    def test_exact_boundary_is_not_returned_as_its_own_next_run(self):
        cron = parse("*/15 * * * *")
        after = datetime(2024, 1, 1, 10, 15, 0)
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 1, 10, 30))

    def test_fixed_time_rolls_over_to_the_next_day(self):
        cron = parse("30 8 * * *")
        after = datetime(2024, 1, 1, 9, 0)
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 2, 8, 30))

    def test_fixed_time_same_day_if_still_ahead(self):
        cron = parse("30 8 * * *")
        after = datetime(2024, 1, 1, 6, 0)
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 1, 8, 30))

    def test_month_field_skips_ahead_to_january(self):
        cron = parse("0 0 1 1 *")
        after = datetime(2024, 3, 15)
        self.assertEqual(next_run(cron, after), datetime(2025, 1, 1))

    def test_seconds_field_is_honoured(self):
        cron = parse("*/30 * * * * *")
        after = datetime(2024, 1, 1, 10, 0, 5)
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 1, 10, 0, 30))

    def test_defaults_after_to_now(self):
        cron = parse("* * * * *")
        before = datetime.now()
        result = next_run(cron)
        self.assertGreater(result, before)


class NextRunDayOfWeekOrDayOfMonthTests(unittest.TestCase):
    def test_weekday_field_alone_matches_on_days_of_that_weekday(self):
        cron = parse("0 9 * * 1")  # every Monday
        after = datetime(2024, 1, 1)  # a Monday
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 8, 9, 0))

    def test_both_restricted_fields_are_or_ed_together(self):
        # fires on the 1st of the month OR any Monday, whichever comes first
        cron = parse("0 9 1 * 1")
        after = datetime(2024, 1, 1, 9, 0)  # Monday the 1st itself, already past
        self.assertEqual(next_run(cron, after), datetime(2024, 1, 8, 9, 0))

    def test_leap_day_schedule_only_fires_on_leap_years(self):
        cron = parse("0 0 29 2 *")
        after = datetime(2023, 3, 1)
        self.assertEqual(next_run(cron, after), datetime(2024, 2, 29))


class NextRunUnsatisfiableScheduleTests(unittest.TestCase):
    def test_impossible_calendar_date_raises(self):
        cron = parse("0 0 30 2 *")  # February never has a 30th
        with self.assertRaises(CronValidationError):
            next_run(cron, datetime(2024, 1, 1))
