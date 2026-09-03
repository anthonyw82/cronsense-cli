# cronsense

Cron expressions are terse enough that it's easy to write one that's
syntactically fine but does the wrong thing: `0-59/5` versus `*/5`, a day-of-week
range that quietly wraps because `7` and `0` are both Sunday, a month field
with a typo'd name that some parsers silently ignore instead of rejecting.
cronsense parses a 5-field cron expression, validates every field against
what cron actually allows, and prints back what the schedule means in plain
English (or JSON, for scripting).

It does not run jobs or compute next-fire times yet - see the roadmap below.

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
```

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
from cronsense import parse, describe

cron = parse("*/15 * * * *")
print(describe(cron))       # "every 15 minutes"
print(str(cron))            # normalized form: "*/15 * * * *"
```

`parse()` raises `CronValidationError` (a `ValueError` subclass) with a
field-specific message on bad input.

## What's supported

- Standard 5-field cron: minute, hour, day-of-month, month, day-of-week.
- `*`, lists (`1,15,30`), ranges (`1-5`), and steps (`*/5`, `1-20/5`).
- Month names (`JAN`-`DEC`) and day names (`SUN`-`SAT`), case-insensitive.
- The day-of-week quirk where both `0` and `7` mean Sunday.
- A trailing command, if present, is preserved but not interpreted.

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

## License

MIT, see LICENSE.
