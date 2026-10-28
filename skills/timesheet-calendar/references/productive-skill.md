# Productive AI skill prompt

Shown to the user during setup and after imports. Paste into Productive AI chat once to create the skill. The user fills in the meetings placeholders.

```
Create a skill called Import calendar time and meetings for my time tracking.

When I invoke it for a date or range:

Read my connected calendar in my local timezone. Process only events that have ended.

Import work events that clearly identify a Productive project and service. Use the event's duration, local start time and title or description, and link the entry to the calendar event.

Link the named task when it can be identified confidently. A broader existing task is acceptable if it clearly matches. If the project and service are clear but the task isn't, log without a task if permitted and flag it. Don't guess a project or service.

Before creating an entry, check whether the event is already linked to one. Don't create duplicates. If it overlaps manually logged time and it's unclear whether the work is already represented, skip it for review.

After importing work events, check for these meetings:

Meeting titles: [list titles]
Project and monthly budget: [name]
Service: [name]
Task: [name]
Use each occurrence's actual local date and time, including rescheduled occurrences. If an entry already exists but has the wrong or missing service or task, update only those fields.

Summarize the dates processed, entries created or updated, and total time logged. Flag skipped events and entries without tasks, and link the affected project and tasks.

Ask me for any missing mapping details rather than guessing.
```

## Running it

After each import, the user pastes this into Productive AI chat. Fill in `{skill}` from `projects.py pref productive_skill_name` (default `Import calendar time and meetings`) and `{range}` with the imported dates.

```
Use the {skill} skill to log my completed calendar events for {range}. Check for existing entries to avoid duplicates. Use the part of each event title after "|" as the entry's description, word for word, keeping the Jira ticket number at the start (e.g. "#3864 Cart shipping missing"). Pick the project, service and task from the Project, Service and Task lines in the event description, and if a task's name contains the same ticket number, link that task. Report anything you couldn't confidently match.
```
