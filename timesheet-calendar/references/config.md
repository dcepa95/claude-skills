# User defaults

Update this file when the user corrects any of these.

| Setting | Value |
|---|---|
| Target calendar | Tasks Tracking: `c_05b23129fa9bd8388c1306f70fe9a2e74027f5c3048c8310f3bdef168a0b5fca@group.calendar.google.com` (private; synced to Productive) |
| Meetings calendar (read-only) | `diogo@buildinamsterdam.com` |
| Holiday calendar (read-only) | `en.dutch#holiday@group.v.calendar.google.com` |
| Created-events ledger | `~/.claude/timesheet-calendar/created.jsonl` (via `scripts/ledger.py`) |
| Git author regex | `dcepa\|Diogo` |
| Working day | 09:00–18:00, Europe/Amsterdam |
| Lunch (keep free) | 12:30–13:30 |

## Projects

Remembered in `~/.claude/timesheet-calendar/projects.json` (outside the skill folder so it survives skill updates), managed with `scripts/projects.py`. Don't edit the JSON by hand; use `projects.py set`.

## plan.json format

```json
{
  "rows": [
    ["2026-10-26", "09:00", "09:30", "M", "Performance", "Loading optimizations: WIP", "WIP commit 10:23"],
    ["2026-10-26", "13:30", "14:45", "M", "#3864 Cart shipping missing", "Cart shipping missing", "Branch checked out 11:56–14:46"]
  ]
}
```

Column 4 is the project key from the registry. `{YYYY}`/`{MM}` in a project name are filled from each row's date, so ranges across months need nothing special.
