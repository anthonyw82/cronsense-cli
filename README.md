# cronsense

Cron expressions are terse enough that it's easy to write one that's
syntactically fine but does the wrong thing: `0-59/5` versus `*/5`, a day-of-week
range that quietly wraps because `7` and `0` are both Sunday, a month field
with a typo'd name that some parsers silently ignore instead of rejecting.
cronsense parses a cron expression (5-field, or 6-field with a leading
seconds field), validates every field against what cron actually allows,
prints back what the schedule means in plain English (or JSON, for
scripting), and can work out the next time it will run.

It does not run jobs itself.

## Usage

```
$ python -m cronsense.cli "*/15 * * * *"
every 15 minutes

$ python -m cronsense.cli "30 8 * * 1-5"
at 08:30, on Monday through Friday

$ python -m cronsense.cli "0 0 1 1 *"
at 00:00, on day 1 of the month, in January

$ python -m cronsense.cli "90 * * * *"
invalid: minute: 90 is outside the allowed range 0-59

$ python -m cronsense.cli "*/30 * * * * *"
every 30 seconds
```

### Seconds

A schedule with six fields is read as `second minute hour day-of-month
month day-of-week`, the same ordering used by cron variants that support
sub-minute schedules. Five-field schedules are unaffected. Because the
sixth field is only recognised when it plus the five before it all parse as
valid schedule fields, a five-field schedule followed by a one-word command
is still read the old way:

```
$ python -m cronsense.cli "0 3 * * * /usr/bin/backup"
at 03:00
runs: /usr/bin/backup
```

### Named schedules

The usual cron nicknames are accepted in place of the five schedule fields,
and expand to the equivalent standard schedule before being validated:

| Nickname | Equivalent |
| --- | --- |
| `@yearly`, `@annually` | `0 0 1 1 *` |
| `@monthly` | `0 0 1 * *` |
| `@weekly` | `0 0 * * 0` |
| `@daily`, `@midnight` | `0 0 * * *` |
| `@hourly` | `0 * * * *` |

```
$ python -m cronsense.cli "@daily"
at 00:00
```

`@reboot` is rejected: it means "run once at startup" rather than on a
recurring schedule, so it has no equivalent set of cron fields.

### Next run time

`--next` computes the next time the schedule will fire, relative to now:

```
$ python -m cronsense.cli --next "30 8 * * 1-5"
at 08:30, on Monday through Friday
next run: 2024-01-02 08:30:00
```

The day-of-month and day-of-week fields follow cron's usual quirk: if both
are restricted (neither is a bare `*`), a match on either one is enough to
run, rather than requiring both.

### JSON output

```
$ python -m cronsense.cli --json "*/15 * * * *"
{
  "valid": true,
  "input": "*/15 * * * *",
  "normalized": "*/15 * * * *",
  "fields": {
    "minute": "*/15",
    "hour": "*",
    "day_of_month": "*",
    "month": "*",
    "day_of_week": "*"
  },
  "command": "",
  "description": "every 15 minutes"
}
```

Invalid input still exits non-zero but still emits JSON, so it's safe to pipe
into another tool without special-casing stderr:

```
$ python -m cronsense.cli --json "90 * * * *"
{"valid": false, "input": "90 * * * *", "error": "minute: 90 is outside the allowed range 0-59"}
```

If a command follows the five schedule fields (as in a real crontab line),
it's carried along untouched and reported back under `"command"`.

## Library use

```python
from cronsense import parse, describe, next_run

cron = parse("*/15 * * * *")
print(describe(cron))       # "every 15 minutes"
print(str(cron))            # normalized form: "*/15 * * * *"
print(next_run(cron))       # next matching datetime, relative to now
```

`parse()` raises `CronValidationError` (a `ValueError` subclass) with a
field-specific message on bad input. `next_run()` takes an optional second
argument to search relative to a specific datetime instead of now, and
raises `CronValidationError` if the schedule can't match within the next
eight years (for example day-of-month 30 in a schedule pinned to February).

## What's supported

- Standard 5-field cron: minute, hour, day-of-month, month, day-of-week.
- Optional 6-field form with a leading seconds field.
- `*`, lists (`1,15,30`), ranges (`1-5`), and steps (`*/5`, `1-20/5`).
- Month names (`JAN`-`DEC`) and day names (`SUN`-`SAT`), case-insensitive.
- The day-of-week quirk where both `0` and `7` mean Sunday.
- Named schedules: `@yearly`, `@annually`, `@monthly`, `@weekly`, `@daily`,
  `@midnight`, `@hourly` (`@reboot` is rejected, see above).
- A trailing command, if present, is preserved but not interpreted.
- Next-run-time calculation, including the day-of-month/day-of-week
  either-or quirk.

## Running from source

No dependencies beyond the Python standard library.

```
python -m cronsense.cli "*/15 * * * *"
```

Or install it locally so the `cronsense` command is on your PATH:

```
pip install -e .
cronsense "*/15 * * * *"
```

## Running the tests

```
python -m unittest discover -s tests
```

## License

MIT, see LICENSE.
