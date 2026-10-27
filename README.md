# claude-skills

dcepa95's [Claude Code](https://claude.com/claude-code) skills, packaged as one plugin, `dcepa95`, in a marketplace of the same repo. Skills run as `/dcepa95:<skill>`.

| Skill | What it does |
|---|---|
| [timesheet-calendar](skills/timesheet-calendar/SKILL.md) | Rebuilds worked hours from git history and Claude Code sessions, and adds them as blocks to a private Google Calendar that Productive reads as timesheet suggestions. Daily macOS reminder with a "Do it now" button. |

## Install

```
/plugin install dcepa95 --marketplace dcepa95/claude-skills
```

Or in two steps:

```
/plugin marketplace add dcepa95/claude-skills
/plugin install dcepa95@claude-skills
```

The repo is private: your git needs access to it (SSH key or `gh auth login && gh auth setup-git`). Updates: `/plugin marketplace update claude-skills`.

## timesheet-calendar

Run `/dcepa95:timesheet-calendar`. The first run walks you through setup:

1. Connect Google Calendar to Claude (claude.ai → Settings → Connectors).
2. Create a private calendar for your timesheet blocks, with a name of your choice.
3. Show that calendar in Productive.
4. Pick your meetings and holiday calendars, git author and working day.

Run `/dcepa95:timesheet-calendar setup` to go through it again. `/dcepa95:timesheet-calendar help` lists the shortcuts.

Needs the Google Calendar connector in Claude, Python 3 and git. Optional: the GitHub CLI (`gh`) for PR titles and review time, and macOS for the daily reminder.

Your settings, projects and the list of events the plugin created live in `~/.claude/timesheet-calendar/`, outside the plugin, so updates never touch them. The plugin only ever changes or deletes events it created itself.

### Importing into Productive

The plugin fills your calendar; turning the blocks into time entries happens in Productive. To have Productive AI do that instead of clicking each suggestion, create a skill in Productive with the prompt below. Replace the placeholders in the meetings part with your recurring meetings and where they're logged.

Every block this plugin creates has `Project:`, `Service:` and `Task:` lines in its description, so the skill can map it without guessing.

```
Create a skill called Import calendar time and meetings for my time tracking.

When I invoke it for a date or range:

Read my connected calendar in my local timezone. Process only events that have ended.

Import work events that clearly identify a Productive project and service. Use the event's duration, local start time and title or description, and link the entry to the calendar event.

Link the named task when it can be identified confidently. A broader existing task is acceptable if it clearly matches. If the project and service are clear but the task isn't, log without a task if permitted and flag it. Don't guess a project or service.

Before creating an entry, check whether the event is already linked to one. Don't create duplicates. If it overlaps manually logged time and it's unclear whether the work is already represented, skip it for review.

After importing work events, check for these meetings:

Meeting titles: [list titles]
Project and monthly budget: [name]
Service: [name]
Task: [name]
Use each occurrence's actual local date and time, including rescheduled occurrences. If an entry already exists but has the wrong or missing service or task, update only those fields.

Summarize the dates processed, entries created or updated, and total time logged. Flag skipped events and entries without tasks, and link the affected project and tasks.

Ask me for any missing mapping details rather than guessing.
```

## Developing

Add the checkout as a local marketplace; edits apply on the next session or `/reload-plugins`:

```
/plugin marketplace add ~/Documents/personal/claude-skills
/plugin install dcepa95@claude-skills
```

Check before pushing: `claude plugin validate .`
