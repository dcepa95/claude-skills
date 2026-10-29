---
name: write
description: Write the user's standup update (what they did since the last working day, what's next, blockers), an end-of-day note, a weekly recap or a client-facing weekly summary, from their real activity: git commits, branches, PRs and Claude Code conversations in their project folders, plus today's meetings. Reuses the timesheet-calendar evidence and settings. Asks before posting anywhere. Use this whenever the user asks for a standup, daily update, "what did I do yesterday", "what should I say in standup", an end-of-day or weekly update, a sprint recap, or a summary of the week for a client or PM. Also `settings` and `help`.
---

# Standup

Turn the user's real activity into a short update they can read out or paste, without them having to remember what they did.

Two rules matter most:
- **Only claim what the evidence shows.** Commits, PRs and the user's own prompts are evidence; guesses aren't. When it's unclear whether something finished, say "worked on", not "done".
- **Nothing gets posted without the user picking it.** Copying to the clipboard and saving a file are fine; Slack or any other channel needs their explicit choice in this run.

The evidence comes from the scripts of the `timesheet` plugin, which this plugin depends on: `TS` below is the output of `python3 ${CLAUDE_SKILL_DIR}/scripts/plugin_path.py timesheet` followed by `/skills/log/scripts`. The settings come from there too: projects folder, folders to check, git author, timezone, meetings calendar. This skill's own preferences live in `~/.claude/standup/prefs.json`. The skill runs as `/standup:write` when installed as a plugin, or `/write` as a personal skill; use whichever started this run when you print commands.

## How to ask

Every decision is an `AskUserQuestion` call with 2–4 concrete options: real dates, ticket numbers and PR titles from this run. The likely answer goes first with "(Recommended)" or "(last used)". Bundle independent questions into one call. Don't ask what the request already answers ("yesterday's standup" settles the type). If the user answers in prose, go with it.

## Arguments

- none: ask which update
- `yesterday`, `today`, `week`, `client`, or a date or range: that update
- `settings`: change the format, folders or where updates go, then stop
- `help`: print the list below, then stop

```
/standup:write             pick the update
/standup:write yesterday   standup: last working day and today's plan
/standup:write today       end-of-day note for today
/standup:write week        recap of this week
/standup:write client      plain-language summary of this week for a client or PM
/standup:write settings    format, folders, where it goes
/standup:write help        this list
```

## 0. Start

Run in parallel:

```bash
python3 $TS/config.py show
python3 $TS/projects.py pref last_folders
cat ~/.claude/standup/prefs.json 2>/dev/null
```

If `plugin_path.py` fails, the `timesheet` plugin isn't installed: show the install command it prints, and stop.

**First run** (no `prefs.json`), or `settings`: ask in one call:
- **"How should your standup look?"**, with a `preview` of each built from a made-up day:
  - `Yesterday / Today / Blockers (Recommended)`: three short lists.
  - `By project`: a heading per project, then bullets.
  - `One paragraph`: a few sentences to read out.
- **"Include ticket numbers?"**: `Yes, like #3679 (Recommended)` · `No`
- **"Where do updates usually go?"**: `Clipboard (Recommended)` · `Slack` · `A .md file`

Save the answers to `~/.claude/standup/prefs.json` as `{"format": "…", "tickets": true, "destination": "…"}`.

**Folders**: if `config.py show` says `setup: needed`, ask **"Which folder holds your projects?"** and then which folders in it to check, the same way as the timesheet skill (`config.py guess`, `gather.py discover`), and save them with `config.py set projects_dir` and `projects.py pref last_folders`. Otherwise use `last_folders` without asking. In `settings`, offer to change them.

## 1. Which update

If the argument or request doesn't settle it, ask **"Which update?"**:
- `Standup: <last working day, e.g. Fri 24 Oct> + today` (Recommended before noon)
- `End of day: today, <Tue 28 Oct>` (Recommended after 16:00)
- `This week: <Mon 26 – today>`
- `Client summary: this week`

The last working day is the previous weekday, so Friday on a Monday. A typed date or range works via Other.

## 2. Gather

When the timesheet plugin started this run, the day's evidence and the approved calendar blocks are already in the conversation. Use them instead of running `gather.py` again: the block titles are the agreed task names, so prefer them. Still run the "next" checks below for a standup or end-of-day note.

```bash
python3 $TS/gather.py collect --since <start> --until <end> --skip-session <current-session-id> <folders…>
python3 $TS/projects.py match <folders…>
```

Pass the current session's id (the UUID in your scratchpad or transcript path) to `--skip-session`, so this conversation doesn't count. The output lists, per day, commits, branch switches and the user's prompts to Claude, with each prompt's branch, plus `Branch → PR` and `Branch → ticket` maps. `projects.py match` gives each folder's project name, for grouping.

For the "next" part of a standup or an end-of-day note, also check, per repo with activity in the last two weeks:
- `git status --short` and the current branch: work in progress.
- `gh pr list --author @me --state open --json number,title,url,isDraft,reviewDecision` (if `gh` works): PRs waiting on review, or with changes requested.
- `gh pr checks <n>` for open PRs with activity in the range: failing checks.
- Today's meetings, if the Google Calendar tools are available: `list_events` on the `meetings_calendar` from the config, for today.

## 3. Make sense of it

Group the evidence into tasks: one item per ticket or branch, not per commit or prompt. Then for each:
- **What happened**, in outcome words ("Added the budget alert to the cart", "Fixed Apple Pay failing without a postcode", "Reviewed #3216"). Merged PRs and commits on the default branch are "done". Branches still open are "worked on" or "in review". Investigations that ended without code are "looked into".
- Skip noise: merges of the default branch, branch housekeeping, setup, and prompts that only steer Claude ("continue", "revert that", "make it shorter").
- Keep the user's words for the domain (their names for features, clients and systems), not your own.

**Next**: open PRs waiting on review or changes, branches with uncommitted work, and what the last prompts were heading towards. **Blockers**: changes requested, failing checks, and prompts that end waiting on someone ("waiting for the PO", "can't reproduce", "need access"). Never invent a blocker.

Then confirm in one call:
- **"What's on for today?"** (multiSelect, standup only): up to 4 candidates from "Next" plus today's meetings, as short labels. More via Other.
- **"Any blockers?"** (multiSelect): the detected ones, plus `None`.

## 4. Write

Use the saved format. Keep it short enough to read out in under a minute: 2–5 bullets per section, one line each. Write the way the user talks: if `~/.claude/ship/voice.md` exists, match the tone of its samples (punctuation, casing, special characters or none). Put ticket numbers first when `tickets` is on (`#3679 Budget alert in the cart`).

- **Standup**: last working day, today, blockers.
- **End of day**: today, what's next tomorrow, blockers.
- **Week**: grouped by project, then by ticket: done, in review, still going.
- **Client summary**: for someone who doesn't read code. Group by feature, not by ticket or branch. Say what changed for their users or their team, what's live, what's waiting on them (decisions, content, access), and what's next. No branch names, file names, tools or internal jargon. Ask the user before naming anything that sounds internal.

Show it in a code block, so it's easy to copy.

## 5. Deliver

Ask **"What should I do with it?"**, with the saved destination first as "(last used)":
- `Copy to clipboard`: `pbcopy` on macOS, `xclip -selection clipboard` or `wl-copy` on Linux.
- `Post to Slack`: only if the Slack tools are available (authenticate them first if needed). Ask which channel or person, offering the last one used, show exactly what will be posted, and post only after a final `Post it` · `Cancel`. Save the channel to `prefs.json` as `slack_channel`.
- `Save as a .md file`: `~/.claude/standup/<YYYY-MM-DD>-<type>.md`. Give the full path.

Changes to the text, typed via Other: revise, show the new version, and ask again. Update `destination` in `prefs.json` with what they picked.
