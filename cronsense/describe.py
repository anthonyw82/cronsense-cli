"""Turns a parsed CronExpression into a plain-English sentence.

This covers the combinations that show up in the wild (fixed times, simple
steps, wildcards, weekday ranges). Odder combinations still validate fine,
they just fall back to a more literal, less idiomatic phrasing.
"""

from __future__ import annotations

from .parser import CronExpression, CronField

MONTH_LABELS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

DAY_LABELS = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
]


def _is_wildcard_field(field: CronField) -> bool:
    return len(field.parts) == 1 and field.parts[0].is_wildcard


def _is_single_value_field(field: CronField) -> bool:
    return len(field.parts) == 1 and field.parts[0].is_single_value


def _is_step_all_field(field: CronField) -> bool:
    part = field.parts[0]
    return len(field.parts) == 1 and part.start is None and part.step is not None


def _describe_part(part, labels=None) -> str:
    label = (lambda v: labels[v]) if labels else str

    if part.start is None:
        base = "every value"
    elif part.end is not None:
        base = f"{label(part.start)} through {label(part.end)}"
    else:
        base = label(part.start)

    if part.step is None:
        return base
    if part.start is None:
        return f"every {part.step}"
    return f"{base}, every {part.step}"


def _describe_field(field: CronField, labels=None) -> str:
    return ", ".join(_describe_part(part, labels) for part in field.parts)


def _describe_minute_hour(minute: CronField, hour: CronField) -> str:
    if _is_single_value_field(minute) and _is_single_value_field(hour):
        h = hour.parts[0].start
        m = minute.parts[0].start
        return f"at {h:02d}:{m:02d}"

    if _is_wildcard_field(minute) and _is_wildcard_field(hour):
        return "every minute"

    if _is_step_all_field(minute) and _is_wildcard_field(hour):
        return f"every {minute.parts[0].step} minutes"

    if _is_single_value_field(minute) and _is_wildcard_field(hour):
        return f"at minute {minute.parts[0].start} past every hour"

    if _is_wildcard_field(minute) and _is_step_all_field(hour):
        return f"every minute, every {hour.parts[0].step} hours"

    if _is_single_value_field(minute) and _is_step_all_field(hour):
        return f"at minute {minute.parts[0].start}, every {hour.parts[0].step} hours"

    return f"at minute {_describe_field(minute)}, hour {_describe_field(hour)}"


def _describe_time(second, minute: CronField, hour: CronField) -> str:
    if second is None:
        return _describe_minute_hour(minute, hour)

    if _is_wildcard_field(second) and _is_wildcard_field(minute) and _is_wildcard_field(hour):
        return "every second"

    if _is_step_all_field(second) and _is_wildcard_field(minute) and _is_wildcard_field(hour):
        return f"every {second.parts[0].step} seconds"

    if _is_single_value_field(second) and _is_wildcard_field(minute) and _is_wildcard_field(hour):
        return f"at second {second.parts[0].start} of every minute"

    if (
        _is_single_value_field(second)
        and _is_single_value_field(minute)
        and _is_single_value_field(hour)
    ):
        h = hour.parts[0].start
        m = minute.parts[0].start
        s = second.parts[0].start
        return f"at {h:02d}:{m:02d}:{s:02d}"

    return f"{_describe_minute_hour(minute, hour)}, second {_describe_field(second)}"


def describe(cron: CronExpression) -> str:
    clauses = [_describe_time(cron.second, cron.minute, cron.hour)]

    if not _is_wildcard_field(cron.day_of_month):
        clauses.append(f"on day {_describe_field(cron.day_of_month)} of the month")

    if not _is_wildcard_field(cron.month):
        clauses.append(f"in {_describe_field(cron.month, MONTH_LABELS)}")

    if not _is_wildcard_field(cron.day_of_week):
        clauses.append(f"on {_describe_field(cron.day_of_week, DAY_LABELS)}")

    return ", ".join(clauses)
