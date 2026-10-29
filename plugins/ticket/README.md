# ticket

Install it:

```
/plugin install ticket --marketplace dcepa95/claude-skills
```

Run `/ticket:plan` with a ticket: paste the story, or give a Jira link, a GitHub issue link or `#123`. Add the Figma links if there are any. It plans the work with you before any code is written:

1. Sums up the goal, the acceptance criteria and what's out of scope.
2. Lists the questions the ticket leaves open, like markets, translations, CMS content, loading and error states, rollout, tracking and edge cases.
3. Looks at the Figma designs and notes missing states or breakpoints.
4. Maps where the change fits in the codebase, and which existing features and helpers to reuse.
5. Asks you the open questions, with a suggested answer for each. The ones only the product owner can answer become a message you can send them.
6. Writes the plan (decisions, approach, steps, tests, what's needed before release) and revises it until you're happy.
7. Saves the plan in the repo or outside it, and creates a branch or worktree named after the ticket, using the repo's branch naming. Only if you pick that.

Nothing in your code changes until you approve the plan. Jira links only open when a Jira or Atlassian connector is set up in Claude; otherwise it asks you to paste the text. GitHub issues need the GitHub CLI (`gh`), and designs need the Figma plugin.

Your last choices are remembered in `~/.claude/ticket/prefs.json`. `/ticket:plan help` lists the shortcuts.

See the [plugin README](../../README.md) to install or update.
