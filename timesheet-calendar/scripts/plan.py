#!/usr/bin/env python3
"""Turn a timesheet plan into calendar event payloads, print the dry-run table and flag problems.

Usage: plan.py plan.json [--meetings F] [--existing F] [--holidays F] [--out events.json]
  --meetings  list_events result of the primary calendar (meetings, out-of-office)
  --existing  list_events result of the target calendar (timesheet blocks already there)
  --holidays  list_events result of the public-holiday calendar
Each option can be repeated (e.g. one file per page of results).

plan.json: {"rows": [["2026-10-26", "09:00", "09:30", "M", "Task", "Title", "Evidence"], ...]}
Project keys come from the registry (projects.py); an optional "projects" object in plan.json overrides it.
"""
import argparse, json, os, sys
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projects import load as load_projects, resolve, save as save_projects

TAG = '[timesheet-import · created by Claude]'


def mins(s):
    h, m = map(int, s.split(':'))
    return h * 60 + m


def hm(n):
    return f'{n // 60}:{n % 60:02d}'


def events(files):
    for f in files or []:
        yield from json.load(open(f)).get('events', [])


def timed(e):
    """(day, start_min, end_min) for timed events, None for all-day."""
    s, en = e.get('start', {}).get('dateTime'), e.get('end', {}).get('dateTime')
    if not s:
        return None
    s, en = datetime.fromisoformat(s), datetime.fromisoformat(en)
    return s.date().isoformat(), s.hour * 60 + s.minute, en.hour * 60 + en.minute


def all_day_dates(e):
    s = e.get('start', {}).get('date')
    if not s:
        return []
    start, end = date.fromisoformat(s), date.fromisoformat(e['end']['date'])
    return [date.fromordinal(o).isoformat() for o in range(start.toordinal(), end.toordinal())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('plan')
    ap.add_argument('--meetings', action='append')
    ap.add_argument('--existing', action='append')
    ap.add_argument('--holidays', action='append')
    ap.add_argument('--min-hours', type=float, default=7)
    ap.add_argument('--max-hours', type=float, default=9)
    ap.add_argument('--out', default='events.json')
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    registry = load_projects()
    projects, rows = {**registry['projects'], **plan.get('projects', {})}, sorted(plan['rows'])
    missing = sorted({r[3] for r in rows} - set(projects))
    if missing:
        sys.exit(f'Unknown project keys {missing}: add them with projects.py set')

    meetings, existing, ooo, holidays = defaultdict(list), defaultdict(list), defaultdict(list), {}
    for e in events(a.meetings):
        if TAG in (e.get('description') or ''):
            continue
        if e.get('eventType') in ('OUT_OF_OFFICE', 'outOfOffice'):
            t = timed(e)
            for d in all_day_dates(e) or ([t[0]] if t else []):
                ooo[d].append(e.get('summary') or 'Out of office')
            continue
        me = next((x for x in e.get('attendees', []) if x.get('self')), {})
        t = timed(e)
        if t and me.get('responseStatus') != 'declined':
            meetings[t[0]].append((t[1], t[2], e.get('summary', ''), me.get('responseStatus', 'owner')))
    for e in events(a.existing):
        t = timed(e)
        if t:
            existing[t[0]].append((t[1], t[2], e.get('summary', '')))
    for e in events(a.holidays):
        for d in all_day_dates(e):
            holidays[d] = e.get('summary', 'Holiday')

    out, problems, warnings, tot = [], [], [], defaultdict(int)
    prev = None
    print(f'{"date":10} {"time":11} {"title":70} task')
    for d, s, e, p, task, title, ev in rows:
        pr = resolve(projects[p], d)
        if mins(e) <= mins(s):
            problems.append(f'{d} {s}-{e}: end before start')
        if prev and prev[0] == d and mins(s) < mins(prev[2]):
            problems.append(f'{d} {s}-{e} overlaps previous block {prev[1]}-{prev[2]}')
        for ms, me_, name, status in meetings.get(d, []):
            if mins(s) < me_ and ms < mins(e):
                problems.append(f'{d} {s}-{e} "{title}" overlaps meeting "{name}" {hm(ms)} ({status})')
        for xs, xe, name in existing.get(d, []):
            if mins(s) < xe and xs < mins(e):
                problems.append(f'{d} {s}-{e} "{title}" overlaps existing timesheet block "{name}" {hm(xs)}-{hm(xe)}')
        prev = (d, s, e)
        tot[d] += mins(e) - mins(s)
        summary = f'{pr["short"]} | {title}'
        print(f'{d} {s}-{e} {summary[:70]:70} {task}')
        out.append({
            'summary': summary,
            'startTime': f'{d}T{s}:00', 'endTime': f'{d}T{e}:00',
            'colorId': pr['color'],
            'description': f'Project: {pr["project"]}\nService: {pr["service"]}\nTask: {task}\nEvidence: {ev}\n\n{TAG}',
            'useDefaultReminders': False, 'notificationLevel': 'NONE',
        })
    json.dump(out, open(a.out, 'w'), indent=1, ensure_ascii=False)
    for k in {r[3] for r in rows} & set(registry['projects']):
        registry['projects'][k]['last_used'] = date.today().isoformat()
    save_projects(registry)

    print(f'\n{len(out)} new events -> {a.out}')
    for d in sorted(set(tot) | set(existing)):
        mtg = sum(me_ - ms for ms, me_, *_ in meetings.get(d, []))
        old = sum(xe - xs for xs, xe, _ in existing.get(d, []))
        total = tot[d] + old + mtg
        print(f'  {d} {date.fromisoformat(d):%a}: new {hm(tot[d])} + already logged {hm(old)} + meetings {hm(mtg)} = {hm(total)}')
        if tot[d] and date.fromisoformat(d).weekday() >= 5:
            warnings.append(f'{d} is a weekend day: confirm the user wants it logged')
        if d in holidays and tot[d]:
            warnings.append(f'{d} is a public holiday ({holidays[d]})')
        if d in ooo and tot[d]:
            warnings.append(f'{d} has out-of-office ({", ".join(ooo[d])}) but blocks are planned')
        if tot[d] and total < a.min_hours * 60:
            warnings.append(f'{d} only adds up to {hm(total)}')
        if total > a.max_hours * 60:
            warnings.append(f'{d} adds up to {hm(total)}, more than {a.max_hours:g}h')
    print('\nProblems (fix before showing the user):' if problems else '\nNo overlaps or invalid blocks.')
    for x in problems:
        print('  ' + x)
    if warnings:
        print('\nWarnings (mention to the user):')
        for x in warnings:
            print('  ' + x)


if __name__ == '__main__':
    main()
