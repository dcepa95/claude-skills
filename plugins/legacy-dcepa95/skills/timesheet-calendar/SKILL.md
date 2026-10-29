---
name: timesheet-calendar
description: The user's dcepa95 plugins moved from the old "claude-skills" marketplace to the "dcepa95" marketplace, and this old install no longer updates. Use this whenever /dcepa95:timesheet-calendar runs, including from the daily timesheet reminder, or when the user asks to fill their timesheet while only the old dcepa95@claude-skills plugin is installed. It moves the install over, keeping their plugins and timesheet settings.
---

# Move to the dcepa95 marketplace

The plugins this command used to run now live in the `dcepa95` marketplace: the timesheet is `/timesheet:log`, and `default@dcepa95` picks which plugins to install. This old install (`dcepa95@claude-skills`) can't update to it on its own.

1. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/migrate.py plan`. It lists the plugins the user has now, which will be kept (timesheet always), and the commands.
2. Tell the user in two lines: the plugins moved to a new marketplace name, and moving takes one step. Their timesheet settings, projects and history in `~/.claude/timesheet-calendar/` stay as they are, and the daily reminder is updated on the first `/timesheet:log` run.
3. Ask **"Move to the new marketplace now?"**:
   - `Move now (Recommended)`: "Removes claude-skills, adds dcepa95, installs default@dcepa95 with <plugins>"
   - `Show me the commands`: print them from the plan in a code block, so the user can run them later.
   - `Not now`
4. On `Move now`, run `python3 ${CLAUDE_SKILL_DIR}/scripts/migrate.py run` and show its output. If a step fails, show the error and the remaining commands.
5. Tell the user to restart Claude Code. The next session installs the plugins, after which `/timesheet:log` works. If they came here to fill their timesheet, they can run `/timesheet:log` with the same request after restarting.
