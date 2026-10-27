# claude-skills

Personal [Claude Code](https://claude.com/claude-code) skills.

| Skill | What it does |
|---|---|
| [timesheet-calendar](timesheet-calendar/SKILL.md) | Rebuilds worked hours from git history and Claude Code sessions, and adds them as blocks to a private Google Calendar that Productive reads as timesheet suggestions. Daily macOS reminder with a "Do it now" button. Run `/timesheet-calendar help` for shortcuts. |

## Install

Clone anywhere and link each skill into `~/.claude/skills`:

```sh
git clone git@github.com:dcepa95/claude-skills.git ~/Documents/personal/claude-skills
ln -s ~/Documents/personal/claude-skills/timesheet-calendar ~/.claude/skills/timesheet-calendar
```

Needs the Google Calendar connector in Claude, Python 3, and optionally the GitHub CLI (`gh`) for PR titles and reviews. Per-user data (projects, created-events ledger, preferences) lives in `~/.claude/timesheet-calendar/`, outside the repo.
