# standup

Run `/dcepa95:standup` to get your standup update written from what you actually did: git commits, branches, PRs and your Claude Code conversations in the project folders you picked, plus today's meetings.

It can write:

- **Standup**: your last working day (Friday on a Monday), today's plan, and blockers.
- **End of day**: today, what's next, and blockers.
- **Week**: this week by project and ticket: done, in review, still going.
- **Client summary**: this week in plain language for a client or PM, with no branch names or jargon.

It groups the work by ticket instead of listing every commit, only claims what the history shows, and asks you to confirm today's plan and any blockers it found, like PRs with changes requested or failing checks. If you've set up your PR samples for [ship](../ship/README.md), it matches their tone.

The update is shown in the chat first. Then you choose: copy it to the clipboard, save it as a `.md` file, or post it to Slack. It only posts after you confirm the channel and the exact text.

The timesheet skill also offers it at the end of each import, reusing the time it just logged.

It reuses the [timesheet-calendar](../timesheet-calendar/README.md) settings: projects folder, folders to check, git author, timezone and meetings calendar. If you haven't set that skill up, the first run asks for the folders. Needs Python 3 and git. Optional: the GitHub CLI (`gh`) for PRs and checks, the Google Calendar connector for meetings, and the Slack connector for posting.

`/dcepa95:standup settings` changes the format and where updates go. `/dcepa95:standup help` lists the shortcuts. Preferences are kept in `~/.claude/standup/prefs.json`.

See the [plugin README](../../README.md) to install or update.
