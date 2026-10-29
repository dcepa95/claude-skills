# claude-skills

dcepa95's [Claude Code](https://claude.com/claude-code) skills, packaged as one plugin, `dcepa95`, in a marketplace of the same repo. Skills run as `/dcepa95:<skill>`.

| Skill | What it does |
|---|---|
| [timesheet-calendar](skills/timesheet-calendar/SKILL.md) | Rebuilds worked hours from git history and Claude Code sessions, and adds them as blocks to a private Google Calendar that Productive reads as timesheet suggestions. Daily macOS reminder with a "Do it now" button. |
| [ship](skills/ship/SKILL.md) | Gets a branch ready for review: reverts leftover TEMP changes, flags new TODOs, reviews the diff, lists translations, CMS changes and env vars needed before release, and writes the PR description in your voice. Asks before opening a PR, or saves the description to a .md file. |

The plugin also installs the [TEMP/TODO guard](#temptodo-guard), which runs in every session.

## Install

```
/plugin install dcepa95 --marketplace dcepa95/claude-skills
```

Or in two steps:

```
/plugin marketplace add dcepa95/claude-skills
/plugin install dcepa95@claude-skills
```

The repo is private: your git needs access to it (SSH key or `gh auth login && gh auth setup-git`).

## Updating

Each run checks GitHub for a newer version first and offers to update. To update by hand:

```
claude plugin marketplace update claude-skills
claude plugin update dcepa95@claude-skills
```

Then restart Claude Code. `claude plugin list` shows the installed version as a commit ID, which should match the latest commit here. If you use the daily reminder, run `/dcepa95:timesheet-calendar reminder on` once afterwards to refresh it. New settings a version needs are asked for on the next run.

To update automatically, turn on auto-update for the `claude-skills` marketplace in `/plugin` → Marketplaces.

## timesheet-calendar

Run `/dcepa95:timesheet-calendar`. The first run walks you through setup:

1. Connect Google Calendar to Claude (claude.ai → Settings → Connectors).
2. Create a private calendar for your timesheet blocks, with a name of your choice.
3. Show that calendar in Productive.
4. Pick the folder that holds your projects, and which folders in it to check.
5. Pick your meetings and holiday calendars, git author and working day.

Run `/dcepa95:timesheet-calendar setup` to go through it again. `/dcepa95:timesheet-calendar help` lists the shortcuts.

Needs the Google Calendar connector in Claude, Python 3 and git. Optional: the GitHub CLI (`gh`) for PR titles and review time, and macOS for the daily reminder.

Your settings, projects and the list of events the plugin created live in `~/.claude/timesheet-calendar/`, outside the plugin, so updates never touch them. The plugin only ever changes or deletes events it created itself.

### Importing into Productive

The plugin fills your calendar; turning the blocks into time entries happens in Productive. Create this skill once in Productive AI, replacing the bracketed placeholders with your timezone, your recurring meetings, and the project, service and task those meetings are logged on.

The skill reads the `Project:`, `Service:` and `Task:` lines every block carries, plus the `Jira:` or `GitHub:` ticket link when there is one, so it maps blocks without guessing. Ticket blocks become two bullets in Productive: the linked ticket number, then the task.

```
Name: Import calendar time and meetings

Description: Logs completed personal-calendar work into Productive, then assigns named meetings to a meetings task without duplicates.

Instructions:
Use this workflow when asked to import personal calendar time for a date range. Apply it to the date or range requested, not a fixed date.

Scope and safety
Confirm the requested date range. Use [your timezone, e.g. Europe/Amsterdam] time.
Process only events that have already ended. Never log future calendar events.
Do not duplicate time: before creating an entry, check whether an entry already links to the same calendar event. If a matching entry already exists, leave it unchanged unless it is missing a service or task that can be resolved confidently.
Keep existing manually logged time intact. If a calendar event overlaps manual time and it is unclear whether it is already represented, do not create a second entry; report it for review.

1. Import personal-calendar work first
Read personal calendar events in the requested period. Prioritize events whose description explicitly names a Productive project, service, and task, especially imported work events.
Pick the project, service, and task from the Project, Service, and Task lines in the event description. Resolve them in Productive; do not guess if the project or service cannot be confidently resolved.
For the time-entry description, use the portion of the event title after the first |, removing only surrounding whitespace. If there is no |, use the event title as written. Do not add project, service, evidence, or import metadata.
When the title begins with a ticket number and the calendar description provides its ticket link (a "Jira:" or "GitHub:" line), format the time-entry description as two bullet points on separate lines: first the ticket number linked to that URL, then the remaining task description word for word. For example: - [#3864](ticket URL) followed by - Cart shipping missing. If no matching link is available, keep the title text as written without inventing a link.
If a task name in the resolved project contains the same ticket number, link that task when the match is unambiguous. Otherwise resolve the task named in the event description; use a broader existing developer task only if it is an unambiguous match. If the task cannot be resolved confidently but the project and service can, log against the service without a task and report the missing task. If a task is mandatory, leave the event unlogged and report it.
Use the event duration and local start time, and link the time entry to the source calendar event.

2. Process existing meeting events
After work-event imports, process these personal calendar meeting titles: [meeting titles, e.g. Daily Stand Up, Refinement].
Explicitly check for each of them on each date in the requested range, including rescheduled recurring occurrences. Use the occurrence's actual local start date and time, not the original date embedded in its event identifier.
Assign each completed occurrence to [project or budget, e.g. "Client Sprints" for that month], its [service] service, and the [meetings task] task.
First check for an existing time entry linked to the meeting calendar event. If it exists but lacks the correct service or task, load it and update only those fields. If no time entry exists, create one for the event duration, with the event title as the note and the calendar event linked.

Output
Briefly state the dates processed, the number of entries created or updated, and total logged time.
Report anything that could not be matched confidently, including entries logged without a task, and list events skipped because they were future or overlapped existing manual time.
Link the affected project and any identified tasks in the final response.
```

After each import, run it from Productive AI chat, with the name you gave the skill and the dates you imported:

```
Use the Import calendar time and meetings skill to log my completed calendar events for [date or date range].
```

## Developing

Add the checkout as a local marketplace. Claude Code runs a copy of the last commit, so commit, then run `claude plugin update dcepa95@claude-skills` (or accept the skill's update prompt) and restart:

```
/plugin marketplace add ~/Documents/personal/claude-skills
/plugin install dcepa95@claude-skills
```

Check before pushing: `claude plugin validate .`

## ship

Run `/dcepa95:ship` on a finished branch. The first run asks you to paste 2–5 PR descriptions you wrote yourself, so the descriptions it writes sound like you. They're saved in `~/.claude/ship/voice.md`. Run `/dcepa95:ship voice` to add or replace them.

Each run:

1. Picks the base branch (the existing PR's base, the branch it's stacked on, or the default branch) and asks what to do with uncommitted changes.
2. Finds leftover `TEMP` changes and offers to revert them, and lists new TODOs.
3. Has a subagent review the diff, and fixes the findings you pick.
4. Lists what must exist before release: translation keys, CMS content, env vars, scripts.
5. Writes the PR description, then asks: open a PR (or draft, or update the existing one), or save it to `~/.claude/ship/drafts/` and copy it to the clipboard.

Nothing is pushed, committed or opened unless you pick it. `/dcepa95:ship pr` writes only the description, and `/dcepa95:ship help` lists the shortcuts. Opening PRs needs the GitHub CLI (`gh`). Without it, you get the file and a link to open the PR yourself.

## TEMP/TODO guard

When you ask Claude for something temporary (a hardcoded value, a forced flag, a service turned on locally, debug logs), it marks each change with a `TEMP:` comment. Before Claude runs `git commit`, `git push` or `gh pr create`, a hook checks the lines that would ship:

- **TEMP comments block the command.** Claude has to revert them, or ask you first. "Revert the temporary changes" finds them all.
- **New TODO/FIXME comments get a warning.** The command still runs, and Claude tells you about them.

Only added lines count, so old TODOs don't trigger it, and Markdown files are skipped. It only guards commands Claude runs. Commits you make yourself aren't checked.

To check a branch by hand:

```
python3 <plugin dir>/hooks/markers.py scan --base develop
```

