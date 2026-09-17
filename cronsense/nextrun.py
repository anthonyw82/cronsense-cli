"""Computes the next time a parsed cron schedule will fire.

The search walks forward one field at a time (month, then day, then hour,
then minute, then second) rather than checking every second between `after`
and the answer. Whenever a field doesn't match, the candidate jumps straight
to the start of the next value for that field, so even a schedule that only
fires once a year resolves in a handful of steps instead of scanning
seconds for months.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .parser import CronExpression, CronField, CronValidationError

# How far ahead to search before giving up. A schedule that never matches
# (e.g. day-of-month 31 in February, with day-of-week left as a bare "*")
# would otherwise search forever.
_SEARCH_LIMIT = timedelta(days=365 * 8)


def next_run(cron: CronExpression, after: datetime = None) -> datetime:
    """Return the next time the schedule fires, strictly after `after`.

    `after` defaults to now. Both it and the result are naive datetimes,
    interpreted as local time, matching how crontab schedules normally run.
    """
    if after is None:
        after = datetime.now()

    candidate = _start_of_next_second(after) if cron.has_seconds else _start_of_next_minute(after)
    deadline = candidate + _SEARCH_LIMIT

    while candidate < deadline:
        if not field_matches(cron.month, candidate.month):
            candidate = _first_of_next_month(candidate)
            continue

        if not _day_matches(cron, candidate):
            candidate = _start_of_next_day(candidate)
            continue

        if not field_matches(cron.hour, candidate.hour):
            candidate = _start_of_next_hour(candidate)
            continue

        if not field_matches(cron.minute, candidate.minute):
            candidate = _start_of_next_minute(candidate)
            continue

        if cron.has_seconds and not field_matches(cron.second, candidate.second):
            candidate = candidate + timedelta(seconds=1)
            continue

        return candidate

    raise CronValidationError(
        f"schedule never matches within {_SEARCH_LIMIT.days} days of {after}"
    )


def field_matches(field: CronField, value: int) -> bool:
    """Whether `value` (a real calendar/clock value) satisfies `field`."""
    return any(_part_matches(field, part, value) for part in field.parts)


def _part_matches(field: CronField, part, value: int) -> bool:
    if part.start is None:
        return part.step is None or (value - field.spec.low) % part.step == 0
    if part.end is not None:
        if not part.start <= value <= part.end:
            return False
        return part.step is None or (value - part.start) % part.step == 0
    if part.step is None:
        return value == part.start
    return value >= part.start and (value - part.start) % part.step == 0


def _is_restricted(field: CronField) -> bool:
    part = field.parts[0]
    return len(field.parts) > 1 or part.start is not None or part.step is not None


def _day_matches(cron: CronExpression, candidate: datetime) -> bool:
    dom_ok = field_matches(cron.day_of_month, candidate.day)
    dow_value = (candidate.weekday() + 1) % 7  # python Monday=0 -> cron Sunday=0
    dow_ok = field_matches(cron.day_of_week, dow_value)

    # cron's documented quirk: when day-of-month and day-of-week are both
    # restricted (neither is a bare "*"), a match on either is enough to
    # run. Otherwise the unrestricted field matches everything anyway, so
    # "and" reduces to just checking the restricted one.
    if _is_restricted(cron.day_of_month) and _is_restricted(cron.day_of_week):
        return dom_ok or dow_ok
    return dom_ok and dow_ok


def _first_of_next_month(dt: datetime) -> datetime:
    year, month = dt.year, dt.month + 1
    if month > 12:
        year, month = year + 1, 1
    return datetime(year, month, 1)


def _start_of_next_day(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day) + timedelta(days=1)


def _start_of_next_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def _start_of_next_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0) + timedelta(minutes=1)


def _start_of_next_second(dt: datetime) -> datetime:
    return dt.replace(microsecond=0) + timedelta(seconds=1)
