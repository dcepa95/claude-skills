---
name: pr
description: Get a finished branch ready for review. Checks for leftover TEMP and TODO comments, reviews the diff, lists what must exist before release (translation keys, CMS content, env vars), and writes the PR description in the user's own voice, learned from real PRs they pasted. Then asks whether to open (or update) the PR or save the description to a .md file. Never pushes or opens a PR without asking. Use this whenever the user wants to ship, wrap up or finish a branch, asks for a PR message, PR description or commit summary, asks "is this ready for review", "what's needed before release", or wants the translations or Contentful changes for a branch, even if they only say "PR message" or "wrap this up". Also `voice` to add or replace their PR samples, `pr` for the description only, and `help`.
---

# Ship

Take the current branch from "done coding" to "ready for review": nothing temporary left in, a fresh pair of eyes on the diff, a list of what has to exist before release, and a PR description that sounds like the user wrote it.

Two rules matter most:
- **Nothing leaves the machine without the user picking it.** No push, PR, PR edit or commit unless they chose that option in this run.
- **The description sounds like the user's own PRs.** Their pasted samples are the reference, not general rules about tone.

Data lives in `~/.claude/ship/`, outside the skill, so updates never touch it: `voice.md` holds the pasted PRs, `drafts/` the saved descriptions. The leftover scanner comes with the `temp-guard` plugin, which this plugin depends on: `MARKERS` below is the output of `python3 ${CLAUDE_SKILL_DIR}/scripts/plugin_path.py temp-guard` followed by `/hooks/markers.py`. If `plugin_path.py` fails, show the install command it prints, and stop. The skill runs as `/ship:pr` when installed as a plugin, or `/pr` as a personal skill; use whichever started this run when you print commands.

## How to ask

Every decision is an `AskUserQuestion` call with 2–4 concrete options: real branch names, file names and counts from this run, with the consequence in the description. Bundle independent questions into one call. Don't ask what the request already answers ("PR into develop" means the base is settled). If the user answers in prose, go with it.

## Arguments

- none: full run
- a branch name (`develop`, `feat/foo`): use it as the base
- `pr`: only steps 1 and 5–6 (context, description, deliver)
- `voice`: manage the PR samples, then stop
- `help`: print the list below, then stop

```
/ship:pr            check, review, release list, PR description
/ship:pr <base>     same, against <base>
/ship:pr pr         PR description only
/ship:pr voice      add, replace or show your PR samples
/ship:pr help       this list
```

## 0. Start

Read `~/.claude/ship/voice.md`. If it's missing or has no samples, or the argument is `voice`, go to "Voice samples" first.

## Voice samples

The description should read like the user wrote it, and the only reliable way to get that is their real PRs. Explain that in two lines, then ask in plain text (not `AskUserQuestion`, since this needs pasting):

> Paste 2–5 PR descriptions you wrote yourself, titles included, in one message. Put a line with `---` between them. Pick typical ones, not your longest.

Then end your turn and wait. When they reply:
1. Fewer than 2 samples: ask **"Two or more samples work better. Add another?"** with `Paste another` and `Continue with one`.
2. Write `~/.claude/ship/voice.md` with the samples **verbatim**, each under `## Sample N`, and above them a `## Style` section of 4–6 short bullets on what you notice: typical length, bullets or prose, headings, casing, punctuation (em dashes, emoji, special characters or none), how they open, ticket references, words they reuse.
3. Show the style bullets and ask `Looks right` · `Add more samples`.

For the `voice` argument with samples already saved, ask **"What do you want to do with your PR samples?"**: `Add more` · `Replace all` · `Show them`. Update the Style section whenever samples change.

## 1. Context

```bash
git fetch origin --quiet
git rev-parse --show-toplevel
git branch --show-current
git status --porcelain
git symbolic-ref --short refs/remotes/origin/HEAD   # default branch
command -v gh >/dev/null && gh pr view --json number,url,baseRefName,title,body,isDraft
```

- On the default branch: say there's nothing to ship from it and stop.
- **Base**: an existing PR's base wins, then the argument. Otherwise check whether the branch is stacked: if a local or remote branch other than the default is an ancestor of `HEAD` and fewer commits away than the default, ask **"Which branch does this go into?"** with that branch first and the default second. If not, use the default without asking.
- **Uncommitted changes**: ask **"There are uncommitted changes in <n> files. What should I do?"**:
  - `Commit them first`: propose a commit message in the voice of the samples, show the files, and commit on confirmation.
  - `Leave them out`: carry on with what's committed and mention it at the end.
  - `Stop`.

Unless the argument is `pr`, ask in the same call **"Which steps should I run?"** (multiSelect): `Code review` · `Release checklist` · `PR description`. The leftover check always runs. Run what they pick, in the order below.

## 2. Leftovers

```bash
python3 $MARKERS scan --base <base>
```

It prints the lines this branch adds that carry `TEMP` or `TODO`/`FIXME` comments, as `TEMP <file>:<line>: <text>`.

**TEMP** lines are temporary changes the user asked for during the work. Show them grouped by file and ask **"Found <n> temporary changes. Revert them?"**:
- `Revert them (Recommended)`: undo each change, not just its comment. Use `git diff <base>...HEAD -- <file>` to see what the marked line replaced, and restore that. Show the resulting diff, then ask `Commit "Remove temporary changes"` · `I'll commit myself`.
- `Keep them`: say that the plugin's hook blocks pushes and PRs while TEMP comments are in the branch. If they still want to keep one, remove only its `TEMP` comment and leave the code.
- `Stop`.

**TODO/FIXME** lines are a warning. List them and ask **"<n> new TODOs. What should I do with them?"**:
- `Keep, and list them in the PR (Recommended)`
- `Keep, don't mention them`
- `Stop, I'll deal with them first`

Nothing found: say so in one line and move on.

## 3. Code review

Launch a review subagent (`Agent`, general-purpose) in the background, so it reviews the code without being anchored on your view. Do step 4 while it runs. Brief it with:
- repo path, branch, base, and `git diff <base>...HEAD` as the change to review; it may read any file it needs;
- report only real problems: bugs, regressions, missed edge cases, wrong assumptions about data, security, performance, accessibility. Skip style and naming nits;
- per finding: `file:line`, severity (high/medium/low), what breaks and when, a one-line fix;
- make no edits.

Show the findings as a numbered list, most severe first. Then ask **"Which should I fix?"** (multiSelect): up to 3 findings by short name, plus `None`. More can be typed via Other as numbers. The user often knows context the reviewer doesn't (business rules, flows that can't happen). When they reject a finding, drop it without arguing.

Fix what they pick. Then run the project's own checks on the changed files: lint, type check and tests, from the `package.json` scripts or equivalent. Show the diff and ask `Commit the fixes` · `I'll commit myself`.

## 4. Release checklist

From the diff, work out what has to exist outside the code before this can go live. Check how the project does each of these (look at existing usages near the changed code) rather than guessing:

- **Translations**: new, renamed or removed keys. Show a table: namespace or resource set | key | value (the default or fallback from the code, `?` if there is none). Values with variables keep them as placeholders.
- **CMS**: new or changed content types, fields, entries, assets or redirects in Contentful, Storyblok, Sanity and the like.
- **Config**: new env vars (`process.env.*`, `NEXT_PUBLIC_*`) and where they must be set (local, preview, production), feature flags, third-party settings (consent categories, payment methods, tag manager tags for new dataLayer events).
- **Scripts**: migrations or one-off scripts to run, and when.

Leave out the sections that don't apply. If nothing applies, say "Nothing needed before release."

## 5. PR description

Re-read `~/.claude/ship/voice.md`, the samples more than the Style notes. Write a title and body that the user could have written:
- Match the samples' length, structure, casing, punctuation and wording. If they never use em dashes, emoji, headings or bold, neither do you. A three-line sample means a three-line description.
- Say what changed and why, from the diff and commit messages. Don't describe the review or this run.
- Never invent testing, screenshots, ticket numbers or links. Take a ticket number from the branch name (`feature/3679-collective-budget` → 3679) only if the samples reference tickets, and use their format.
- Add the release checklist and the kept TODOs only when there are any, in the samples' style.
- For a stacked branch, add one line saying where it sits ("2 of 3, based on feat/x").
- When updating an existing PR, start from its current body and keep what still holds.

Show the title and body in a code block, so it's easy to copy.

## 6. Deliver

Always ask; never skip this. **"What should I do with the description?"**:
- `Open a PR into <base>`, or `Update PR #<n>` when one exists: "Pushes <branch> and opens the PR on GitHub"
- `Open a draft PR into <base>` (leave it out when a PR already exists)
- `Save to a .md file`: "Saves it and copies it to the clipboard. Nothing is pushed"

Changes to the text, typed via Other: revise, show the new version, and ask again.

**Open or update a PR**:
1. Check `gh auth status`. Without a working `gh`, or with a remote that isn't GitHub, say so, save the file as below, and for GitHub give the compare link `https://github.com/<owner>/<repo>/compare/<base>...<branch>?expand=1`.
2. Write the body to a file in the scratchpad directory.
3. `git push -u origin <branch>`. If the TEMP hook blocks it, go back to step 2.
4. `gh pr create --base <base> --title '<title>' --body-file <file>` (add `--draft` for a draft), or `gh pr edit <n> --title '<title>' --body-file <file>`.
5. Print the PR URL.

**Save to a .md file**: write `~/.claude/ship/drafts/<repo>/<branch, with / replaced by ->.md` holding `# <title>`, a blank line, then the body. Copy the title and body to the clipboard (`pbcopy` on macOS, `xclip -selection clipboard` or `wl-copy` on Linux, if present). Give the full path.

End with one short summary: what was reverted, fixed and committed, what's still uncommitted, and where the description went.
