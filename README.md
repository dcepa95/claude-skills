# claude-skills

dcepa95's [Claude Code](https://claude.com/claude-code) skills, packaged as one plugin, `dcepa95`, in a marketplace of the same repo. Skills run as `/dcepa95:<skill>`.

| Skill | What it does |
|---|---|
| [timesheet-calendar](skills/timesheet-calendar/README.md) | Rebuilds worked hours from git history and Claude Code sessions, and adds them as blocks to a private Google Calendar that Productive reads as timesheet suggestions. Daily macOS reminder with a "Do it now" button. |
| [ship](skills/ship/README.md) | Gets a branch ready for review: reverts leftover TEMP changes, flags new TODOs, reviews the diff, lists translations, CMS changes and env vars needed before release, and writes the PR description in your voice. Asks before opening a PR, or saves the description to a .md file. |
| [ticket](skills/ticket/README.md) | Turns a ticket and its Figma links into an agreed plan before any code: requirements, open questions, codebase map, a message for the PO, and a branch or worktree named after the ticket. |

The plugin also installs the [TEMP/TODO guard](hooks/README.md), which runs in every session: it stops Claude from committing, pushing or opening a PR while temporary changes are in, and warns about new TODOs.

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

## Developing

Add the checkout as a local marketplace. Claude Code runs a copy of the last commit, so commit, then run `claude plugin update dcepa95@claude-skills` (or accept the skill's update prompt) and restart:

```
/plugin marketplace add ~/Documents/personal/claude-skills
/plugin install dcepa95@claude-skills
```

Check before pushing: `claude plugin validate .`
