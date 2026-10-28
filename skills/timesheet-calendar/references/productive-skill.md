# Productive AI skill

Shown to the user during setup and after imports. The user creates this skill once in Productive AI, replacing the bracketed placeholders (timezone, meeting titles, and the project, service and task meetings are logged on). It reads the `Project:`, `Service:`, `Task:` and `Jira:`/`GitHub:` lines this plugin writes into each block.

```
Name: Import calendar time and meetings

Description: Logs completed personal-calendar work into Productive, then assigns named meetings to a meetings task without duplicates.

Instructions:
Use this workflow when asked to import personal calendar time for a date range. Apply it to the date or range requested, not a fixed date.

Scope and safety
Confirm the requested date range. Use [your timezone, e.g. Europe/Amsterdam] time.
Process only events that have already ended. Never log future calendar events.
Do not duplicate time: before creating an entry, check whether an entry already links to the same calendar event. If a matching entry already exists, leave it unchanged unless it is missing a service or task that can be resolved confidently.
Keep existing manually logged time intact. If a calendar event overlaps manual time and it is unclear whether it is already represented, do not create a second entry; report it for review.

1. Import personal-calendar work first
Read personal calendar events in the requested period. Prioritize events whose description explicitly names a Productive project, service, and task, especially imported work events.
Pick the project, service, and task from the Project, Service, and Task lines in the event description. Resolve them in Productive; do not guess if the project or service cannot be confidently resolved.
For the time-entry description, use the portion of the event title after the first |, removing only surrounding whitespace. If there is no |, use the event title as written. Do not add project, service, evidence, or import metadata.
When the title begins with a ticket number and the calendar description provides its ticket link (a "Jira:" or "GitHub:" line), format the time-entry description as two bullet points on separate lines: first the ticket number linked to that URL, then the remaining task description word for word. For example: - [#3864](ticket URL) followed by - Cart shipping missing. If no matching link is available, keep the title text as written without inventing a link.
If a task name in the resolved project contains the same ticket number, link that task when the match is unambiguous. Otherwise resolve the task named in the event description; use a broader existing developer task only if it is an unambiguous match. If the task cannot be resolved confidently but the project and service can, log against the service without a task and report the missing task. If a task is mandatory, leave the event unlogged and report it.
Use the event duration and local start time, and link the time entry to the source calendar event.

2. Process existing meeting events
After work-event imports, process these personal calendar meeting titles: [meeting titles, e.g. Daily Stand Up, Refinement].
Explicitly check for each of them on each date in the requested range, including rescheduled recurring occurrences. Use the occurrence's actual local start date and time, not the original date embedded in its event identifier.
Assign each completed occurrence to [project or budget, e.g. "Client Sprints" for that month], its [service] service, and the [meetings task] task.
First check for an existing time entry linked to the meeting calendar event. If it exists but lacks the correct service or task, load it and update only those fields. If no time entry exists, create one for the event duration, with the event title as the note and the calendar event linked.

Output
Briefly state the dates processed, the number of entries created or updated, and total logged time.
Report anything that could not be matched confidently, including entries logged without a task, and list events skipped because they were future or overlapped existing manual time.
Link the affected project and any identified tasks in the final response.
```

## Running it

After each import, the user pastes this into Productive AI chat. Fill in `{skill}` from `projects.py pref productive_skill_name` (default `Import calendar time and meetings`) and `{range}` with the imported dates. The rules live in the skill, so this stays one line.

```
Use the {skill} skill to log my completed calendar events for {range}.
```
