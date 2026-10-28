---
name: timesheet-calendar
description: Reconstruct what the user worked on (from git commits, reflogs and Claude Code conversations in folders they choose), lay it out as time blocks within the working day, and import those blocks as events into a private Google Calendar of their choosing so Productive can turn them into timesheet entries. Use this whenever the user wants to fill in timesheets, log hours, track or reconstruct what they worked on for a day/week/month, fill timesheet gaps, or add work blocks to their calendar or Productive, even if they only say "do it for today" or "what did I work on last week" in a timesheet context. Also use it to manage the skill's settings (projects and colours, task naming, the work folder, the default terminal, and the daily timesheet reminder on/off/time) and to show its shortcut commands (`help`) or redo setup (`setup`).
---

# Timesheet → Calendar

Rebuild the user's working days from evidence, agree on the blocks with them, then create calendar events Productive picks up as timesheet suggestions.

The user's calendar is shared with colleagues and holds real meetings, so the two things that matter most are: **never touch an event you didn't create in this flow**, and **never write to the calendar before the user approves a dry run**. Everything else is judgement.

Personal settings (calendars, git author, working day, lunch) and data live in `~/.claude/timesheet-calendar/`, outside the skill; `references/config.md` describes them. Scripts are in `${CLAUDE_SKILL_DIR}/scripts`. The skill is invoked as `/dcepa95:timesheet-calendar` when installed as a plugin, or `/timesheet-calendar` as a personal skill; use whichever form started this run when you print commands.

## Setup (first run)

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/config.py show` at the start of every run. If its last line says `setup: needed`, or the argument is `setup`, guide the user through the steps below before anything else.

Go one step at a time. Each step that needs the user to act elsewhere ends with a question: `Done` (Recommended) · `I'm stuck`, with what "done" looks like in the description. On `I'm stuck`, ask what they see and help, then ask again. Don't move on before `Done`. Skip any step that's already true, such as a connector that's already working. Open with two lines on what they'll end up with: a private Google Calendar that only they see, which Claude fills with work blocks and Productive shows as timesheet suggestions.

**1. Connect Google Calendar to Claude.** Check whether the Google Calendar tools (`list_calendars`, `create_event`, …) are available, and call `list_calendars`.
- If it works, say which account is connected and go to step 2.
- If the tools exist but need authentication (an `authenticate` tool, or an auth error), run the authenticate tool, then tell the user to finish the sign-in in the browser with their **work** Google account.
- If there are no Google Calendar tools at all, explain:
  1. On claude.ai, go to Settings → Connectors → Google Calendar → Connect, and sign in with the work Google account.
  2. Back in Claude Code, logged in with the same claude.ai account, run `/mcp` to check that it's listed and connected, or restart Claude.

  Then ask `Done` · `I'm stuck`. Once the tools appear, call `list_calendars` to confirm.

**2. Choose the calendar's name.** Ask **"What should your timesheet calendar be called?"**:
- `Tasks Tracking (Recommended)`
- `Timesheet`
- `Work log`

Any other name goes via Other. If `list_calendars` already shows a secondary calendar the user owns that looks like one, offer `Use "<name>", which I found` first.

**3. Create the calendar.** The connector can't create calendars, so give the steps:
1. Open calendar.google.com with the work account.
2. In the left sidebar, next to **Other calendars**, click **+** → **Create new calendar**.
3. Name it `<chosen name>` and click **Create calendar**.
4. Optional: in its settings, under **Access permissions**, check that it isn't shared, so only you see it.

Ask `Done` · `I'm stuck`. Then call `list_calendars` again and find it by name. If it's missing, say so and ask again; it can take a moment to show up. Never fall back to the primary calendar, because colleagues can see it.

**4. Show it in Productive.** Explain that Productive must read this calendar for the blocks to become timesheet suggestions:
1. In Productive, open the Google Calendar integration, connect the same Google account, and tick `<chosen name>` in the calendars it shows. See [Productive's guide](https://help.productive.io/en/articles/6940914-google-calendar-integration).
2. Under **My time → Calendar view**, events from it appear as grey suggestions.

Ask `Done` · `Skip for now (I'll do it later)`. Skipping is fine; the first import offers a test event to check it.

**4b. Create the import skill in Productive AI.** Explain that the calendar blocks still have to become time entries in Productive, and that Productive AI can do that in one go. Show the prompt from `references/productive-skill.md` in a code block, so it's easy to copy. Tell the user to:
1. Paste it into Productive AI chat, which creates the skill "Import calendar time and meetings".
2. Replace the meetings placeholders with their recurring meetings and the project, budget, service and task those are logged on.

Ask `Done` · `Later`. On `Done`, run `projects.py pref productive_skill done`. If they named the skill differently in Productive, save that with `projects.py pref productive_skill_name '<name>'`.

**5. The rest, in one call.** Run `config.py guess`, then ask:
- **Meetings calendar**: the primary calendar (Recommended), read only.
- **Holidays**: holiday calendars from `list_calendars` (e.g. `Holidays in Netherlands`), plus `None`.
- **Git author**: the `guess` value (Recommended), the name alone, or the email name alone. It's the regex matched against commit authors.
- **Working day**: `09:00–18:00, lunch 12:30–13:30 (Recommended)` · `08:30–17:30, lunch 12:00–13:00` · `10:00–19:00, lunch 13:00–14:00`

**6. Save and confirm.** Run `config.py set` for each value:
- `target_calendar`: the new calendar's ID
- `meetings_calendar`
- `holiday_calendar`
- `author`
- `workday` and `lunch`, written as `HH:MM-HH:MM`

Then show `config.py show` and say what happens next: the user picks folders, Claude reads their history and proposes blocks, and nothing is written before they approve. Carry on with what they asked for. With `setup` alone, stop here.

The reminder question comes at the end of the first run (see step 5 of the main flow).

## How to ask

The user should be able to get through a whole run by picking options, typing only when they want something unusual. So every decision point below is an `AskUserQuestion` call, not a prose question:

- 2–4 options per question, the likely answer first with "(Recommended)" or "(last used)". "Other" is always added automatically for free text, so never add your own "Other" option.
- Make options concrete: real dates, folder names, hours, block titles from this run, not "Option A". Put the consequence in the description ("Skips Tue 27, 0 blocks created").
- Bundle independent questions into one call (up to 4) instead of asking one after another. Questions that depend on an earlier answer or on script output wait for it.
- Use `preview` when options differ in what they'd produce (naming styles, a day's blocks).
- Don't ask what's already been answered: in the request ("do today" → skip the range question), in remembered prefs, or earlier in the run.
- If the user answers in prose instead, go with it.

## 0. Start

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py gaps` first. It prints the last day with logged blocks and the weekdays of the last two weeks with nothing logged, which makes the range options concrete.

If the argument is a shortcut (see "Shortcuts and help"), handle it and stop. If the request already names a range or an action, skip this question. Otherwise ask **"What do you want to log?"**:
- `Today (<Mon 27 Oct>)` (Recommended late in the day)
- `Missing days (<Thu 23, Mon 27>)`: the weekdays `gaps` reported, only if there are any. Recommended when there are earlier gaps.
- `Yesterday` or `This week so far`, whichever fits better
- `Settings`: go to "Settings" below.

A typed range ("October", "14–18 Oct") works via Other. Weekdays only unless the user says otherwise.

## 1. Folders, projects and manual entries

Run discovery:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gather.py discover <parent-dir> --since <start-date>
python3 ${CLAUDE_SKILL_DIR}/scripts/projects.py match <every discovered dir>
python3 ${CLAUDE_SKILL_DIR}/scripts/projects.py pref last_folders
```

`<parent-dir>` is the working directory the user started Claude in, the folder they chose. If that directory is itself a git repo, use its parent. Then one `AskUserQuestion` call:

**"Which folders in `<parent-dir>` should I scan?"** (multiSelect). Every option is one real folder, labelled with its exact name (`mammut-ecom-platform-2`). Don't use group labels like "Same as last time", project names, or "both checkouts".
- In each description, put the commit and session counts in the range, the project it matches, and "(last used)" if it's in `last_folders`.
- Order: folders with activity first, most active first, then other git repos in `<parent-dir>`, marked "no activity in range".
- With more than 4 folders, split them over several multiSelect questions in the same call (`Folders 1/2`, `Folders 2/2`), up to 4 per question. Leave out folders with no activity beyond that; the user can type any folder via Other.

Ask about manual entries in the same call, if the folder questions leave room (4 questions per call at most; otherwise ask it next):

**"Did you log any of these days in Productive by hand?"** (Productive's own entries are invisible from here.) Options: `No (Recommended)`, then one per day in the range for up to 3 days (multiSelect), or `Yes, some days` for longer ranges, followed by a day picker. Skip that question for a single day in favour of a yes/no.

Save the folder choice: `projects.py pref last_folders '<dir>,<dir>'`.

### New projects

For every chosen folder `match` reports as `UNKNOWN`, set the project up before collecting evidence. One call, three questions:
- **Project** in Productive: existing projects first when the folder might belong to a known client (a new checkout of a known repo), else a guess from the folder name.
- **Service**: the services already used by that project, or a sensible guess (`Development`, `Development hours`).
- **Colour**: run `projects.py colors` first. Offer three unused colours as `🟧 Tangerine`-style labels. Put the full list in the question text so any other can be typed. Mention that `! python3 ${CLAUDE_SKILL_DIR}/scripts/projects.py colors` shows real swatches.

Save: `projects.py set <KEY> --short '<Client · Service>' --project '<name, with {YYYY}/{MM} if per month>' --service '<service>' --color <name or id> --folders '<glob>'`. Use a glob that covers sibling checkouts (`repo*`).

If a folder matches the wrong project, fix the entry with `projects.py set` instead of working around it.

## 2. Collect evidence

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gather.py collect --since <start> --until <end> --skip-session <current-session-id> <dir> [<dir> ...]
```

Pass the current session's id (the UUID in your scratchpad or transcript path) to `--skip-session` so this conversation doesn't count as work. Output is per day:
- commits (a commit seen in several checkouts is listed once)
- reflog checkouts and merges
- Claude Code prompts with their branch
- when the GitHub CLI is set up: PRs opened or merged, PR reviews and a branch → PR title map

Days are marked `(WEEKEND)`. If GitHub was skipped, mention once that `brew install gh && gh auth login` adds PR titles and review time, then move on. Save long output to the scratchpad.

Fetch three things from Google Calendar for the range with `list_events` (`startTime`, `endTime`, `pageSize: 250`), using the calendar IDs from `config.py show`, and save each to a scratchpad file:
- **Meetings**: the primary calendar. Out-of-office events come back here too.
- **Already logged**: the timesheet calendar (`target_calendar`). Re-runs fill gaps only.
- **Holidays**: the public-holiday calendar.

Follow any `nextPageToken` and pass both pages.

## 3. Build the blocks

**Naming.** If there's a branch → PR map, ask **"How should tasks be named?"** with options `PR title` and `Branch name`, each with a real example from this run in `preview` (`#3864 Cart shipping missing` vs `#3864 - Show shipping costs in cart summary`). Put the value of `projects.py pref title_source` first, marked "(last used)". Save with `projects.py pref title_source pr|branch`. Without a PR map, use branch names and don't ask.

Turn evidence into blocks within the `workday` hours, as `[date, start, end, projectKey, task, title, evidence]`:
- Evidence marks **when** something was happening, not how long it took. Be generous: assume work started well before a commit and continued until the next sign of different work. A branch checked out from 11:56 to 14:46 filled that span.
- Leave meetings uncovered and keep `lunch` free.
- Absorb gaps of 15 minutes or less into the neighbouring block, or leave them out. No 10-minute blocks.
- Leave time already covered by events in the timesheet calendar alone.
- Tidy branch names (`story/#3864-cart-shipping-missing` → `#3864 Cart shipping missing`). Branches without a PR always use the branch name.
- Start the title with the Jira ticket number when the work has one. `gather.py` prints a `Branch → ticket` map, taken from the number at the start of the branch name (`fix/3891-account-nav` → `#3891`, `feature/#3905-#3906-wishlist` → `#3905 #3906`). Without a ticket from the branch, look up `projects.py pref 'ticket:<branch or title>'`. If that's empty, ask in step 4. Never use the PR number in its place, except for release blocks.
- Keep the rest of the title very short, like a ticket name: 2–4 words, at most about 30 characters after the number. Examples: `#3864 Cart shipping missing`, `#3891 Account nav underline`, `Forms reCAPTCHA`, `Contentful redirects`, `Review budget branch`, `Release #3230 / #3205`. Name the topic, not the work done on it: no colons with explanations, no "check if…" or "resolve … server side". Details go in the evidence column of the dry run; it never reaches the calendar. Consecutive blocks on the same topic get the same title.
- PR reviews get their own block (`Review PR #123 …`) in the repo's project.
- Merges into staging/develop, release PRs and cherry-picks are their own `Releases` blocks.
- Stretches with no evidence: infer from the task in progress before and after, and say "inferred" in the evidence. Don't invent specific work.
- Weekends, holidays and out-of-office days get no blocks unless the evidence clearly shows work.
- Don't fill time that hasn't happened yet today.
- Take the project from the folder the evidence came from.

Write the plan JSON (format in `references/config.md`) and run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/plan.py plan.json --meetings <file> --existing <file> --holidays <file> --out events.json
```

It prints the dry-run table, per-day totals (new + already logged + meetings), then two lists:
- **Problems**: overlaps with meetings, existing blocks or each other. Fix them all and re-run before showing anything. A meeting with no response still counts; a declined one doesn't.
- **Warnings**: these become questions in step 4, not silent fixes.

## 4. Dry run → decisions → confirmation

Show the dry-run table per day (time, title, task, evidence), the meetings left uncovered, what was already logged, and the totals. Then ask, bundled into as few calls as possible:

**One question per warning or judgement call**, each with options specific to it:

| Situation | Options |
|---|---|
| Day under 7h (`Thu 23: 5h 15m`) | `Leave it (half day)` · `Fill the gaps with inferred work` · `Skip the day` |
| Day over 9h | `Keep it` · `Trim to 9h (drop the last inferred block)` |
| Blocks on a weekend, holiday or OOO day | `Keep them` · `Drop them` |
| Block without a ticket number (not a release, review or inferred block) | One question per topic, not per block, up to 4 per call: **"Does `<title>` have a Jira ticket?"**. Options: `No ticket`, plus `#<n> <name>` for tickets seen nearby in the evidence that could fit. Any other ticket is typed via Other as `#1234 Ticket name`. With a ticket, the title becomes `#1234 <short ticket name>`, following the short-title rule. Remember the answer with `projects.py pref 'ticket:<branch or title>' '#1234 Ticket name'` (or `none`), and check that pref before asking, so the same topic isn't asked again. |
| Inferred stretches | multiSelect `Which inferred blocks should I keep?`, one option per block (title + time), up to 4. If there are more, use one option per day. |
| An existing block in the timesheet calendar looks wrong given new evidence | `Leave it` · `Replace it with <new title>` (only if `ledger.py has` succeeds; otherwise only `Leave it` and tell the user) |

Apply the answers, re-run `plan.py`, and show the table again only if something changed.

**Then the go-ahead.** Ask **"Import <N> blocks (<h> h) into <timesheet calendar name>?"**:
- `Import all (Recommended)`
- `Test event first`: creates only the first block so the user can check Productive. Recommended instead for a first import or a range longer than a week.
- For ranges of several days: `Choose days`, followed by a multiSelect of the days. Use one option per day for up to 4 days, otherwise one per week.
- `Change something`: the user says what in Other or in prose. Update the plan, re-run, and ask again.

Nothing is written to the calendar before an import option is picked. "Other" text that isn't a clear yes counts as a change request.

After a test event, ask `Shows up in Productive, import the rest` · `Doesn't show up` (troubleshoot: is the timesheet calendar ticked in Productive's Google Calendar integration? See setup step 4.).

## 5. Import

Create each event from `events.json` with `create_event` on the timesheet calendar (`target_calendar`), passing every field as is (`summary`, `startTime`, `endTime`, `colorId`, `description`, `useDefaultReminders: false`, `notificationLevel: NONE`). Send parallel batches of at most 10.

After **each** batch, record what came back before sending the next:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py add <calendarId> '<id>|<YYYY-MM-DDTHH:MM>|<summary>' [...]
```

The ledger (`~/.claude/timesheet-calendar/created.jsonl`) outlives the conversation; the scratchpad doesn't. It is what proves an event is yours.

**Failures.** Record what did come back. Work out which planned events are still missing by matching start times against the ledger, and retry only those. For quota errors (`Resource has been exhausted`, rate limits): run `sleep 60` with `run_in_background`, continue when it finishes, and halve the batch size. If the same events fail a second time, ask `Retry in a minute (Recommended)` · `Stop here, finish later`. A later run fills the gap without duplicating, so stopping is safe. Never resend a whole batch blindly.

**Verify** by listing the timesheet calendar for the range (`list_events` with `calendarId`, `startTime`, `endTime`; no full-text search) and running:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py verify <list_events file> --since <start> --until <end>
```

Recreate anything reported missing, then verify again.

Report: events created per day and the verification result. Then tell the user the next step is in Productive, because nothing is logged there yet:
- If `projects.py pref productive_skill` is `done`, give the run prompt from `references/productive-skill.md` ("Running it") in a code block, with the skill name and the imported range filled in, ready to paste into Productive AI chat.
- Otherwise, explain that Productive AI needs the import skill once. Show the prompt from `references/productive-skill.md` as in setup step 4b, then the run prompt. Ask `Created it` (saves the pref) · `I'll add them by hand`. Adding them by hand means clicking each grey suggestion in My time → Calendar view after refreshing. Then, if `reminder.py status` says `never set up`, ask the reminder question from Settings once. "No thanks" runs `reminder.py off`, which records the choice so it isn't asked again.

## Shortcuts and help

The skill takes shortcut arguments, so settings can be changed without going through a run. Match the argument loosely ("change terminal to iterm" = `terminal iterm`). A shortcut with a value applies it straight away and confirms in one line. Without a value, it asks the matching question from Settings.

| Shortcut | Does |
|---|---|
| `help` | shows this list with the current values |
| `setup` | walks through setup again: Google Calendar connection, timesheet calendar, Productive, git author, working day |
| `settings` | the settings menu |
| `folder` · `folder <path>` · `folder reset` | the work folder: where **Do it now** starts Claude, so its subfolders are what gets scanned. `reset` makes the next **Do it now** ask again. |
| `terminal` · `terminal <app>` · `terminal ask` · `terminal always` | the default terminal for **Do it now**. `ask` shows the picker each time with the default preselected; `always` opens the default without asking. |
| `reminder` · `reminder on` · `reminder off` · `reminder 17:00` · `reminder daily` · `reminder weekdays` | the daily reminder |
| `projects` | add, rename or recolour projects |
| `naming` · `naming pr` · `naming branch` | name tasks after PR titles or branch names |
| `productive` | shows the Productive AI skill prompt again |
| `today` · `yesterday` · `this week` · `missing` · `14–18 Oct` | log hours for that range (anything else is read as a range or a request) |

**`help`** runs `reminder.py status` and `projects.py pref title_source`, then prints the table above with a "Now" column showing the current values. Under it, it lists the terminal equivalents, which work without starting Claude:

```
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py status
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py folder ~/work
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py terminal iTerm --ask off
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py on --time 17:00 --days weekdays
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py off
! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py test
! python3 ${CLAUDE_SKILL_DIR}/scripts/projects.py list
```

Replace `${CLAUDE_SKILL_DIR}` with the real path when printing. Run nothing else for `help`.

## Settings

Reached from the start menu, the `settings` shortcut, or when the user asks to change any of these. Run `reminder.py status` first, then ask **"What do you want to change?"**, with each option's description showing its current value:
- `Daily reminder`: on or off, time and days
- `Work folder`: the folder **Do it now** starts in
- `Terminal`: the default terminal, and whether the reminder asks
- `Projects`: add, rename or recolour

Task naming is changed via Other or the `naming` shortcut.

**Daily reminder.** A dialog shown by `scripts/reminder.py` from a launchd job, so it keeps working after Claude exits and after a restart. Ask **"Daily reminder to log your hours?"**:
- `Weekdays at 17:30 (Recommended)`, or the current setting marked "(current)"
- `Every day at 17:30`
- `Off`

A different time goes via Other. If no work folder is set yet, ask the work folder question in the same call. Run `reminder.py on --time HH:MM --days weekdays|daily [--cwd <dir>]` or `reminder.py off`.

The dialog has three buttons:
- **Do it now**: shows the terminal picker with the default preselected, unless it's set to `always`. It opens a window in the work folder and starts `claude "<command> fill my time for today"`, where the command is `/dcepa95:timesheet-calendar` for the plugin (`reminder.py on` detects it; `--command` overrides).
  - Terminal and iTerm are scripted directly.
  - Apps without a scripting API (Hyper, Ghostty, Warp…) get a new window with the command typed in. That needs Accessibility permission, which macOS asks for once. Nothing is typed unless a new window is confirmed in front; otherwise the command goes to the clipboard.
  - With no work folder set, the first click asks for one.
- **Remind me later…**: 15 minutes to 2 hours.
- **Skip today**.

It closes itself after 10 minutes if ignored. The launchd job runs a copy of `reminder.py` from `~/.claude/timesheet-calendar/bin` (background jobs can't read `~/Documents`), so after changing `reminder.py`, run `reminder.py on` again to refresh the copy. Don't run `reminder.py test` yourself, because it waits for a click; suggest the user runs `! python3 ${CLAUDE_SKILL_DIR}/scripts/reminder.py test`. On anything but macOS, say it isn't supported.

**Work folder.** Ask **"Which folder should Do it now start Claude in?"** Options:
- the current one, marked "(current)"
- the directory this session runs in, if different
- that directory's parent, if it's a git repo
- `Ask me next time`

Show the subfolders each would scan in the description. Run `reminder.py folder <dir>`, or `reminder.py folder --reset` for the last option.

**Terminal.** One call with two questions:
- **"Default terminal?"**: the apps from `reminder.py terminals`, current default first, marked "(current)".
- **"When you click Do it now…"**: `Ask which terminal each time` · `Open the default straight away`.

Run `reminder.py terminal <app> --ask on|off`.

**Projects.** Show `projects.py list`. Ask which project, with each project as an option (`🩷 Mammut · Dev hours`) plus `Add a new project`. Then ask what to change: `Colour` · `Title prefix` · `Productive project/service` · `Remove`. Colour follows the colour question from "New projects", and the rest are typed. Save with `projects.py set|remove`. After a recolour or rename, ask `Update events already created` · `Only future events`, and update only events that `ledger.py has` confirms are yours.

**Task naming.** Ask `PR title` · `Branch name`, then run `projects.py pref title_source pr|branch`.

After any change made from the menu, ask `Done` · `Change something else` · `Log hours now`. Shortcuts with a value just confirm.

## Changing or removing events later

An event is yours to change only if `ledger.py has <id>` succeeds. Anything else (meetings, events the user made, even apparent duplicates) is off limits: tell the user and let them handle it.

Productive copies an event into a separate time entry when the user adds it, and later calendar changes don't reach that entry. So before renaming, moving or deleting blocks, ask **"Have you already added these days to Productive?"**: `No, change the calendar (Recommended)` · `Yes, leave them`. If yes, explain that Productive keeps the old version. Any change must then be made in Productive by hand, and changed events may show up there as suggestions again, which mustn't be added a second time.

Before deleting or changing your own events, list them and ask a multiSelect `Which blocks should I delete?` (title + time per option, grouped by day when there are more than 4). Then confirm with `Delete <N> blocks` · `Cancel`. After deleting, run `ledger.py remove <id>`.

To move events between calendars: create the copies and record them, verify all of them, then delete the originals and mark them removed. Never delete first.

`ledger.py list --since <d> --until <d>` shows what you've created for a range.
