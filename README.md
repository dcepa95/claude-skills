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

Run `/dcepa95:timesheet-calendar`. The first run sets you up: it asks for the private calendar Productive reads, your meetings and holiday calendars, your git author and your working day. `/dcepa95:timesheet-calendar help` lists the shortcuts.

Needs the Google Calendar connector in Claude, Python 3 and git. Optional: the GitHub CLI (`gh`) for PR titles and review time, and macOS for the daily reminder.

Your settings, projects and the list of events the plugin created live in `~/.claude/timesheet-calendar/`, outside the plugin, so updates never touch them. The plugin only ever changes or deletes events it created itself.

## Developing

Add the checkout as a local marketplace; edits apply on the next session or `/reload-plugins`:

```
/plugin marketplace add ~/Documents/personal/claude-skills
/plugin install dcepa95@claude-skills
```

Check before pushing: `claude plugin validate .`
