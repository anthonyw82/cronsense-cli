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


if __name__ == "__main__":
    unittest.main()
