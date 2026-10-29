# claude-skills

dcepa95's [Claude Code](https://claude.com/claude-code) plugins, in one marketplace. Each plugin installs on its own, so you only get what you pick.

| Plugin | Command | What it does |
|---|---|---|
| [timesheet](plugins/timesheet/README.md) | `/timesheet:log` | Rebuilds worked hours from git history and Claude Code sessions, and adds them as blocks to a private Google Calendar that Productive reads as timesheet suggestions. Daily macOS reminder with a "Do it now" button. |
| [standup](plugins/standup/README.md) | `/standup:write` | Writes your standup, end-of-day note, weekly recap or client summary from your commits, PRs and Claude conversations. Asks before posting to Slack. Installs timesheet too. |
| [ship](plugins/ship/README.md) | `/ship:pr` | Gets a branch ready for review: reverts leftover TEMP changes, flags new TODOs, reviews the diff, lists translations, CMS changes and env vars needed before release, and writes the PR description in your voice. Asks before opening a PR. Installs temp-guard too. |
| [ticket](plugins/ticket/README.md) | `/ticket:plan` | Turns a ticket and its Figma links into an agreed plan before any code: requirements, open questions, codebase map, a message for the PO, and a branch or worktree named after the ticket. |
| [design-qa](plugins/design-qa/README.md) | `/design-qa:check` | Checks a page or component against its Figma design: measured properties and a pixel diff, states and breakpoints, a ledger of differences with the file to fix, and optional fix rounds. |
| [temp-guard](plugins/temp-guard/README.md) | none, runs by itself | Stops Claude from committing, pushing or opening a PR while temporary changes marked `TEMP` are in, and warns about new TODOs. |

Claude also uses a skill on its own when your request matches it ("fill my timesheet", "write my standup"), so you don't have to type the command.

## Install

Add the marketplace once:

```
/plugin marketplace add dcepa95/claude-skills
```

Then install the plugins you want, by name:

```
/plugin install timesheet@claude-skills
/plugin install ship@claude-skills
```

Or run `/plugin`, open the `claude-skills` marketplace and pick from the list. Plugins that need another one (standup needs timesheet, ship needs temp-guard) install it with them. Restart Claude Code after installing.

The repo is private: your git needs access to it (SSH key or `gh auth login && gh auth setup-git`).

### Already using `dcepa95`?

`dcepa95` used to hold everything. It now only installs the timesheet plugin, so your timesheet keeps working, under the new command `/timesheet:log`. Its settings in `~/.claude/timesheet-calendar/` stay as they are, and the first run updates the daily reminder to the new command. Install any other plugin you want from the list above.

## Updating

The timesheet plugin checks GitHub for a newer version on each run and offers to update. To update by hand:

```
claude plugin marketplace update claude-skills
claude plugin update <plugin>@claude-skills
```

Then restart Claude Code. `claude plugin list` shows each installed version as a commit ID, which should match the latest commit here. New settings a version needs are asked for on the next run.

To update automatically, turn on auto-update for the `claude-skills` marketplace in `/plugin` → Marketplaces.

## Developing

Each plugin lives in `plugins/<name>/`, with its manifest in `.claude-plugin/plugin.json` and its skill in `skills/<command>/`. The marketplace list is `.claude-plugin/marketplace.json`.

Add the checkout as a local marketplace. Claude Code runs a copy of the last commit, so commit, then run `claude plugin update <plugin>@claude-skills` (or accept the update prompt) and restart:

```
/plugin marketplace add ~/Documents/personal/claude-skills
/plugin install <plugin>@claude-skills
```

To try plugins for one session without installing: `claude --plugin-dir plugins/standup --plugin-dir plugins/timesheet`.

Check before pushing: `claude plugin validate .` for the marketplace, and `claude plugin validate plugins/<name>` for each plugin.
