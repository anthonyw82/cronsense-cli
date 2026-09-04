import unittest

from cronsense.parser import CronValidationError, parse


class ParseWholeExpressionTests(unittest.TestCase):
    def test_rejects_empty_expression(self):
        with self.assertRaises(CronValidationError):
            parse("")

    def test_rejects_whitespace_only_expression(self):
        with self.assertRaises(CronValidationError):
            parse("   \t  ")

    def test_rejects_too_few_fields(self):
        with self.assertRaises(CronValidationError):
            parse("* * * *")

    def test_tolerates_extra_whitespace_between_fields(self):
        cron = parse("*/15   *  *   *  *")
        self.assertEqual(str(cron), "*/15 * * * *")

    def test_trailing_tokens_become_command(self):
        cron = parse("0 3 * * * /usr/bin/backup --full")
        self.assertEqual(cron.command, "/usr/bin/backup --full")
        self.assertEqual(str(cron), "0 3 * * * /usr/bin/backup --full")

    def test_no_command_leaves_it_empty(self):
        cron = parse("* * * * *")
        self.assertEqual(cron.command, "")
        self.assertEqual(str(cron), "* * * * *")


class FieldRangeTests(unittest.TestCase):
    def test_minute_out_of_range_high(self):
        with self.assertRaises(CronValidationError):
            parse("60 * * * *")

    def test_minute_negative(self):
        with self.assertRaises(CronValidationError):
            parse("-1 * * * *")

    def test_hour_out_of_range(self):
        with self.assertRaises(CronValidationError):
            parse("* 24 * * *")

    def test_day_of_month_zero_is_invalid(self):
        with self.assertRaises(CronValidationError):
            parse("* * 0 * *")

    def test_day_of_month_32_is_invalid(self):
        with self.assertRaises(CronValidationError):
            parse("* * 32 * *")

    def test_month_zero_is_invalid(self):
        with self.assertRaises(CronValidationError):
            parse("* * * 0 *")

    def test_month_13_is_invalid(self):
        with self.assertRaises(CronValidationError):
            parse("* * * 13 *")


class NamesTests(unittest.TestCase):
    def test_month_name_is_case_insensitive(self):
        cron = parse("0 0 1 jan *")
        self.assertEqual(str(cron.month), "1")

    def test_day_name_is_case_insensitive(self):
        cron = parse("0 0 * * mon")
        self.assertEqual(str(cron.day_of_week), "1")

    def test_unrecognised_month_name_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("* * * jam *")

    def test_day_of_week_seven_wraps_to_zero(self):
        cron = parse("* * * * 7")
        self.assertEqual(str(cron.day_of_week), "0")

    def test_day_of_week_zero_and_seven_are_equivalent(self):
        self.assertEqual(str(parse("* * * * 0").day_of_week), str(parse("* * * * 7").day_of_week))


class RangeAndStepTests(unittest.TestCase):
    def test_range_start_after_end_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("* * * * 5-1")

    def test_wrap_seven_range_can_invert_after_wrapping(self):
        # 6-7 wraps to 6-0, which then looks like start-after-end.
        with self.assertRaises(CronValidationError):
            parse("* * * * 6-7")

    def test_step_of_zero_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("*/0 * * * *")

    def test_negative_step_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("*/-5 * * * *")

    def test_non_numeric_step_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("*/x * * * *")

    def test_range_with_step(self):
        cron = parse("1-20/5 * * * *")
        self.assertEqual(str(cron.minute), "1-20/5")

    def test_open_ended_range_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("1- * * * *")


class MalformedListTests(unittest.TestCase):
    def test_empty_item_in_list_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("1,,3 * * * *")

    def test_trailing_comma_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("1,3, * * * *")

    def test_non_numeric_value_is_rejected(self):
        with self.assertRaises(CronValidationError):
            parse("abc * * * *")

    def test_list_of_valid_values_round_trips(self):
        cron = parse("1,15,30 * * * *")
        self.assertEqual(str(cron.minute), "1,15,30")


if __name__ == "__main__":
    unittest.main()
