import unittest

from cronsense.describe import describe
from cronsense.parser import parse


class SecondsDescriptionTests(unittest.TestCase):
    def test_five_field_expression_has_no_seconds_clause(self):
        self.assertEqual(describe(parse("*/15 * * * *")), "every 15 minutes")

    def test_all_wildcards_with_seconds_is_every_second(self):
        self.assertEqual(describe(parse("* * * * * *")), "every second")

    def test_seconds_step_with_wildcard_minute_and_hour(self):
        self.assertEqual(describe(parse("*/30 * * * * *")), "every 30 seconds")

    def test_fixed_second_with_wildcard_minute_and_hour(self):
        self.assertEqual(
            describe(parse("15 * * * * *")), "at second 15 of every minute"
        )

    def test_fixed_time_with_seconds(self):
        self.assertEqual(describe(parse("30 15 9 * * *")), "at 09:15:30")

    def test_list_of_seconds_falls_back_to_a_literal_clause(self):
        self.assertEqual(
            describe(parse("1,31 * * * * *")), "every minute, second 1, 31"
        )


class DateFieldDescriptionTests(unittest.TestCase):
    def test_single_day_of_month(self):
        self.assertEqual(
            describe(parse("0 0 15 * *")), "at 00:00, on day 15 of the month"
        )

    def test_day_of_month_range(self):
        self.assertEqual(
            describe(parse("0 0 1-5 * *")), "at 00:00, on day 1 through 5 of the month"
        )

    def test_day_of_month_step_all(self):
        self.assertEqual(
            describe(parse("0 0 */5 * *")), "at 00:00, every 5 days of the month"
        )

    def test_named_month(self):
        self.assertEqual(
            describe(parse("0 0 1 jan *")), "at 00:00, on day 1 of the month, in January"
        )

    def test_month_step_all(self):
        self.assertEqual(describe(parse("0 0 * */3 *")), "at 00:00, every 3 months")

    def test_day_of_week_range(self):
        self.assertEqual(
            describe(parse("0 0 * * mon-fri")),
            "at 00:00, on Monday through Friday",
        )

    def test_day_of_week_list(self):
        self.assertEqual(
            describe(parse("0 0 * * 1,3,5")),
            "at 00:00, on Monday, Wednesday, Friday",
        )

    def test_day_of_week_step_all(self):
        self.assertEqual(
            describe(parse("0 0 * * */2")), "at 00:00, every 2 days of the week"
        )


if __name__ == "__main__":
    unittest.main()
