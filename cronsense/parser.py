"""Parsing and validation for cron expressions.

A cron schedule is normally five whitespace-separated fields (minute, hour,
day-of-month, month, day-of-week). Some cron variants prepend a seconds
field, giving six fields (second, minute, hour, day-of-month, month,
day-of-week); this parser accepts that form too. Anything after the
schedule fields is treated as the command that would be run, and is carried
along unparsed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class CronValidationError(ValueError):
    """Raised when a cron expression fails validation."""


MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

DAY_NAMES = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}


@dataclass(frozen=True)
class FieldSpec:
    name: str
    low: int
    high: int
    names: Optional[dict]
    # day-of-week is the one field where cron accepts both 0 and 7 for Sunday
    wrap_seven: bool = False


FIELD_SPECS = (
    FieldSpec("minute", 0, 59, None),
    FieldSpec("hour", 0, 23, None),
    FieldSpec("day_of_month", 1, 31, None),
    FieldSpec("month", 1, 12, MONTH_NAMES),
    FieldSpec("day_of_week", 0, 6, DAY_NAMES, wrap_seven=True),
)

SECOND_SPEC = FieldSpec("second", 0, 59, None)

# second, minute, hour, day_of_month, month, day_of_week
FIELD_SPECS_WITH_SECONDS = (SECOND_SPEC,) + FIELD_SPECS


@dataclass(frozen=True)
class FieldPart:
    """One comma-separated piece of a field, e.g. '*/15', '1-5', or '3'."""

    start: Optional[int]  # None means the piece is a bare '*'
    end: Optional[int]    # set only for a-b ranges
    step: Optional[int]   # set only when a '/n' step was given

    @property
    def is_wildcard(self) -> bool:
        return self.start is None and self.step is None

    @property
    def is_single_value(self) -> bool:
        return self.start is not None and self.end is None and self.step is None


@dataclass(frozen=True)
class CronField:
    spec: FieldSpec
    parts: tuple

    def __str__(self) -> str:
        return ",".join(_render_part(p) for p in self.parts)


@dataclass(frozen=True)
class CronExpression:
    minute: CronField
    hour: CronField
    day_of_month: CronField
    month: CronField
    day_of_week: CronField
    second: Optional[CronField] = None
    command: str = ""

    @property
    def has_seconds(self) -> bool:
        return self.second is not None

    @property
    def fields(self):
        base = (self.minute, self.hour, self.day_of_month, self.month, self.day_of_week)
        return (self.second,) + base if self.second is not None else base

    def __str__(self) -> str:
        schedule = " ".join(str(field) for field in self.fields)
        return f"{schedule} {self.command}".rstrip() if self.command else schedule


def _render_part(part: FieldPart) -> str:
    if part.start is None:
        base = "*"
    elif part.end is not None:
        base = f"{part.start}-{part.end}"
    else:
        base = str(part.start)
    return f"{base}/{part.step}" if part.step is not None else base


def _resolve_value(spec: FieldSpec, token: str) -> int:
    if spec.names is not None and token.upper() in spec.names:
        return spec.names[token.upper()]

    if not token.lstrip("-").isdigit():
        raise CronValidationError(f"{spec.name}: '{token}' is not a number or recognised name")

    value = int(token)
    if spec.wrap_seven and value == 7:
        value = 0
    if not spec.low <= value <= spec.high:
        raise CronValidationError(
            f"{spec.name}: {value} is outside the allowed range {spec.low}-{spec.high}"
        )
    return value


def _parse_part(spec: FieldSpec, token: str) -> FieldPart:
    if not token:
        raise CronValidationError(f"{spec.name}: empty value in '{token}'")

    step = None
    base = token
    if "/" in token:
        base, step_text = token.split("/", 1)
        if not step_text.isdigit() or int(step_text) < 1:
            raise CronValidationError(f"{spec.name}: step '{step_text}' must be a positive integer")
        step = int(step_text)

    if base == "*":
        return FieldPart(start=None, end=None, step=step)

    if "-" in base:
        start_text, end_text = base.split("-", 1)
        start = _resolve_value(spec, start_text)
        end = _resolve_value(spec, end_text)
        if start > end:
            raise CronValidationError(f"{spec.name}: range '{base}' has start after end")
        return FieldPart(start=start, end=end, step=step)

    value = _resolve_value(spec, base)
    return FieldPart(start=value, end=None, step=step)


def parse_field(spec: FieldSpec, text: str) -> CronField:
    if not text:
        raise CronValidationError(f"{spec.name}: field is empty")
    parts = tuple(_parse_part(spec, token) for token in text.split(","))
    return CronField(spec=spec, parts=parts)


def _try_parse_fields(specs, tokens):
    """Parse len(specs) leading tokens against specs, or return None if any fail.

    Used to probe whether a run of tokens looks like a valid schedule before
    committing to it, since a six-field schedule and a five-field schedule
    followed by a numeric-looking command are otherwise indistinguishable.
    """
    try:
        return tuple(parse_field(spec, token) for spec, token in zip(specs, tokens))
    except CronValidationError:
        return None


def parse(expression: str) -> CronExpression:
    """Parse and validate a cron schedule, raising CronValidationError on bad input."""
    raw = expression.strip()
    if not raw:
        raise CronValidationError("expression is empty")

    tokens = raw.split()
    if len(tokens) < 5:
        raise CronValidationError(f"expected 5 schedule fields, found {len(tokens)}: '{raw}'")

    if len(tokens) >= 6:
        six_fields = _try_parse_fields(FIELD_SPECS_WITH_SECONDS, tokens[:6])
        if six_fields is not None:
            second, minute, hour, day_of_month, month, day_of_week = six_fields
            command = " ".join(tokens[6:])
            return CronExpression(
                minute, hour, day_of_month, month, day_of_week,
                second=second, command=command,
            )

    field_tokens, command_tokens = tokens[:5], tokens[5:]
    fields = [parse_field(spec, token) for spec, token in zip(FIELD_SPECS, field_tokens)]
    return CronExpression(*fields, command=" ".join(command_tokens))
