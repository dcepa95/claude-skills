---
name: plan
description: Turn a ticket (a pasted Jira or user story, a Jira link, a GitHub issue) plus its Figma links into an agreed implementation plan before any code is written. Pulls out the requirements and acceptance criteria, flags the questions the ticket leaves open (markets, translations, CMS, tracking, flags, states), looks at the designs, maps where it fits in the codebase, asks the open questions, saves the plan, and offers a branch or worktree named after the ticket. Use this whenever the user pastes a ticket or story ("As a customer I want…"), shares a Jira or issue link to work on, says "new ticket", "let's start this feature", "plan this", or asks what's missing from a ticket, even without naming the skill. Also `help`.
---

# Ticket

Get from "here's the ticket" to a plan the user agrees with, so implementation starts with the right questions answered instead of discovering them ten prompts in.

The rule that matters most: **no code changes until the user approves the plan.** Reading, searching and looking at designs are fine. Creating a branch or worktree happens only when they pick it.

Data lives in `~/.claude/ticket/`, outside the skill: `prefs.json` remembers the last choices (where plans go, branch or worktree), `plans/` holds plans saved outside a repo. The skill runs as `/ticket:plan` when installed as a plugin, or `/plan` as a personal skill; use whichever started this run when you print commands.

## How to ask

Every decision is an `AskUserQuestion` call with 2–4 concrete options, the likely answer first with "(Recommended)" or "(last used)". Bundle independent questions into one call (4 at most). Don't ask what the ticket or the user already answered. If they answer in prose, go with it.

## Arguments

- ticket text, a Jira link, a GitHub issue link or `#123`: plan that ticket
- none: ask for it
- `help`: print the list below, then stop

```
/ticket:plan <paste or link>   plan a ticket
/ticket:plan #123              plan a GitHub issue of this repo
/ticket:plan help              this list
```

## 1. Get the ticket

- **Pasted text**: use it as is.
- **GitHub issue** (link or `#123`): `gh issue view <n> --json number,title,body,labels,comments,url`.
- **Jira link**: if a Jira or Atlassian tool is available, fetch the issue with its comments. Otherwise say the link can't be opened from here and ask the user to paste the description.
- **Nothing**: ask in plain text for the ticket text or link, plus any Figma links, then end your turn and wait.

Find the ticket number: from the link, the key in the text (`MCOM-3679` → `3679`, keep the full key for display), or `#123`. If there's none, ask in the next question call with `No ticket number` as an option.

Also note the repo: `git rev-parse --show-toplevel`. If Claude wasn't started in a repo, ask which one, offering the git repos in the current folder.

## 2. Break it down

Write a short summary in the chat:
- **Goal**: one sentence, in plain words.
- **Must do**: the acceptance criteria as a checklist. Number them, so the plan and questions can refer to them.
- **Out of scope**: only what the ticket says, or what's clearly implied.
- **Given**: facts the ticket states that shape the solution (APIs, numbers, copy, deadlines).

Then work out the **open questions**: things the ticket doesn't settle that would change the code. Go through this list and keep only what applies and isn't answered:
- Where: which markets, countries, locales, currencies, sites; logged-in, guest or both; mobile and desktop behaviour.
- Content: new copy and translation keys; CMS content types, fields or entries; who creates them.
- States: loading, empty, error, disabled, very long content, slow or failing APIs.
- Rollout: feature flag, A/B test or for everyone; a date it must go live.
- Tracking: analytics or dataLayer events; consent.
- Data: where it comes from, what's the source of truth, what happens to existing data.
- Edges: limits, rounding, time zones, permissions, accessibility, legal requirements.

Each question gets a recommended answer when the code or the ticket suggests one, so the user can just confirm it.

## 3. Designs

For each Figma link, if the Figma tools are available (load the Figma skills they require first): take a screenshot of the node and read its metadata. List what the design shows (screens, states, breakpoints, variants) and what it's missing compared with step 2 (no mobile, no error state, no hover). Add the gaps to the open questions. Don't generate code from it here.

Without Figma tools, say so, and ask whether to go on without the designs.

## 4. Map the codebase

Launch 1–3 Explore agents in parallel, depending on the ticket's size. Give each a narrow brief:
- where this plugs in: entry points, routes, components, API clients, the flow it changes;
- the closest existing feature to copy patterns from;
- existing helpers to reuse instead of rewriting (formatting, currency, i18n, feature flags, tracking, CMS fetching), and tests that cover the area.

Read the key files yourself afterwards. Check that what the agents report actually exists before you rely on it.

## 5. Ask

Ask the open questions with `AskUserQuestion`, up to 4 per call, most important first. Each one names the criterion it affects, with options built from what you found ("Use the existing `formatCurrency` (Recommended)"). Questions only the client or product owner can answer get the option `Ask the PO`.

Collect the `Ask the PO` ones into a short message the user can send: plain words, numbered, each with the default you'll assume until they answer. If `~/.claude/ship/voice.md` exists, match the tone of its samples.

## 6. Plan

Write the plan:

```markdown
# <KEY or #n>: <ticket title>

<ticket link>  ·  <Figma links>

## Goal
## Decisions
<each answered question: decision and why, one line each>
## Approach
<how it works, in a few sentences: data flow, where state lives, what's reused>
## Steps
<numbered, each one reviewable on its own, with the files it touches; split into stacked PRs when it's big>
## Tests
## Before release
<translations, CMS content, env vars, flags, tracking setup>
## Open
<what's waiting on the PO, with the assumed default>
```

Keep it short: the reader is the user and a reviewer, not a manager. Show it in the chat and ask **"Does this plan work?"**: `Looks good` · `Change something` (typed via Other). Revise until it's `Looks good`.

## 7. Save and set up

Read `~/.claude/ticket/prefs.json` (it may not exist). Then ask in one call:

**"Where should I save the plan?"**
- `In the repo (docs/plans/<number>-<slug>.md)`: the user decides whether to commit it.
- `Outside the repo (~/.claude/ticket/plans/<repo>/<number>-<slug>.md)`
- `Don't save it`

**"Set up a branch?"**
- `New worktree`: recommended for bigger work, or when the current checkout has uncommitted changes.
- `New branch here`
- `Not now`

Name the branch after the repo's convention: look at `git branch -a --sort=-committerdate` for the last 30 branches (`feature/3679-collective-budget`, `fix/…`) and use the same prefix and pattern, with a 2–4 word slug. Put the proposed name in the option descriptions; a different name goes via Other.

- **Worktree**: `git fetch origin`, find the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD`), then `git worktree add ../<repo>-<slug> -b <branch> origin/<default>`. Symlink the untracked env files from the main checkout (`.env`, `.env.local`, `.dev.vars`…), don't copy them. Tell the user the path; Claude has to be started there, or use `EnterWorktree` if it's available.
- **Branch here**: only with a clean working tree; otherwise offer the worktree instead. `git fetch origin && git switch -c <branch> origin/<default>`.

Save both choices to `prefs.json` (`{"plans": "repo|outside|none", "branch": "worktree|here|none"}`) and offer them as "(last used)" next time.

## 8. Hand off

End with the plan's location, the branch or worktree, and the PO message if there is one. Then ask **"Start on step 1?"**: `Yes` · `Not now`.
