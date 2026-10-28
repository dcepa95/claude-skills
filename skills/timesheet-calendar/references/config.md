# Settings and data

Everything personal lives in `~/.claude/timesheet-calendar/`, outside the skill, so installs and updates never touch it:

| File | Holds | Managed with |
|---|---|---|
| `projects.json` → `config` | calendars, git author, working day, lunch, timezone | `scripts/config.py show / set` |
| `projects.json` → `projects` | projects, colours, folder globs, ticket link pattern (Jira or GitHub) | `scripts/projects.py` |
| `projects.json` → `prefs` | task naming, last folders, reminder settings | `projects.py pref`, `reminder.py` |
| `created.jsonl` | every event this skill created (the only events it may change) | `scripts/ledger.py` |
| `bin/` | copy of the reminder scripts the launchd job runs | `reminder.py on` |

Don't edit the JSON by hand.

## Settings (`config.py show`)

| Key | Default | Meaning |
|---|---|---|
| `target_calendar` | required | the private calendar blocks are created in; Productive must read it |
| `meetings_calendar` | `primary` | where meetings are read from, never written |
| `holiday_calendar` | none | public holidays, read only |
| `author` | required | git `--author` regex, `a\|b` for several names |
| `projects_dir` | required | folder holding all project checkouts; scanned each run |
| `workday` | `09:00-18:00` | hours blocks are planned in |
| `lunch` | `12:30-13:30` | kept free |
| `timezone` | this machine's | IANA name |

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
