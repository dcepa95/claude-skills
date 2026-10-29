# ship

Install it (this also installs [temp-guard](../temp-guard/README.md)):

```
/plugin install ship --marketplace dcepa95/claude-skills
```

Run `/ship:pr` on a finished branch. The first run asks you to paste 2–5 PR descriptions you wrote yourself, so the descriptions it writes sound like you. They're saved in `~/.claude/ship/voice.md`. Run `/ship:pr voice` to add or replace them.

Each run:

1. Picks the base branch (the existing PR's base, the branch it's stacked on, or the default branch) and asks what to do with uncommitted changes.
2. Finds leftover `TEMP` changes and offers to revert them, and lists new TODOs.
3. Has a subagent review the diff, and fixes the findings you pick.
4. Lists what must exist before release: translation keys, CMS content, env vars, scripts.
5. Writes the PR description, then asks: open a PR (or draft, or update the existing one), or save it to `~/.claude/ship/drafts/` and copy it to the clipboard.

Nothing is pushed, committed or opened unless you pick it. `/ship:pr pr` writes only the description, and `/ship:pr help` lists the shortcuts. Opening PRs needs the GitHub CLI (`gh`). Without it, you get the file and a link to open the PR yourself.

See the [plugin README](../../README.md) to install or update.
