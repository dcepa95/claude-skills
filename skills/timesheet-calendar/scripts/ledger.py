#!/usr/bin/env python3
"""Permanent record of calendar events this skill created. Only events in here may be edited or deleted.

Usage:
  ledger.py add CALENDAR_ID 'ID|START[|SUMMARY]' [...] record created events (START = 2026-10-26T09:00)
  ledger.py list [--since YYYY-MM-DD] [--until YYYY-MM-DD]
  ledger.py has ID [ID ...]                           exit 1 if any id is not ours
  ledger.py remove ID [ID ...]                        mark events as deleted (after delete_event succeeded)
  ledger.py update ID [--summary S] [--start T]       record an in-place edit (after update_event succeeded)
  ledger.py imported DATE [...]                        mark days as added to Productive (--undo to unmark)
  ledger.py imported --check DATE [...]                say which days are already in Productive
  ledger.py verify LIST_EVENTS_JSON --since D --until D
                                                      compare a list_events result of the target calendar with the ledger
  ledger.py gaps [--days N]                           last logged day, weekdays in the last N days (default 14) with nothing logged,
                                                      and days with blocks not yet in Productive
"""
import argparse, json, os, sys
from datetime import date, datetime, timedelta, timezone

LEDGER = os.path.expanduser(os.environ.get('TIMESHEET_LEDGER', '~/.claude/timesheet-calendar/created.jsonl'))
IMPORTED = os.path.join(os.path.dirname(LEDGER), 'imported.json')


def imported():
    return json.load(open(IMPORTED)) if os.path.exists(IMPORTED) else {}


def entries():
    """Live entries keyed by id (later lines win)."""
    out = {}
    if os.path.exists(LEDGER):
        for line in open(LEDGER):
            if line.strip():
                e = json.loads(line)
                out[e['id']] = e
    return {k: v for k, v in out.items() if not v.get('deleted')}


def append(rows):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, 'a') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def in_range(e, since, until):
    d = e['start'][:10]
    return (not since or d >= since) and (not until or d <= until)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    a_ = sub.add_parser('add')
    a_.add_argument('calendar')
    a_.add_argument('items', nargs='+')
    l = sub.add_parser('list')
    l.add_argument('--since')
    l.add_argument('--until')
    h = sub.add_parser('has')
    h.add_argument('ids', nargs='+')
    r = sub.add_parser('remove')
    r.add_argument('ids', nargs='+')
    v = sub.add_parser('verify')
    v.add_argument('file')
    v.add_argument('--since', required=True)
    v.add_argument('--until', required=True)
    g = sub.add_parser('gaps')
    g.add_argument('--days', type=int, default=14)
    u = sub.add_parser('update')
    u.add_argument('id')
    u.add_argument('--summary')
    u.add_argument('--start')
    im = sub.add_parser('imported')
    im.add_argument('dates', nargs='+')
    im.add_argument('--check', action='store_true')
    im.add_argument('--undo', action='store_true')
    a = ap.parse_args()
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    if a.cmd == 'add':
        known = entries()
        rows = []
        for it in a.items:
            eid, start, *summary = it.split('|', 2)
            if eid in known:
                continue
            rows.append({'id': eid, 'calendar': a.calendar, 'start': start, 'summary': summary[0] if summary else '', 'created': now})
        append(rows)
        print(f'Recorded {len(rows)} new event(s) in {LEDGER}')
    elif a.cmd == 'list':
        done = imported()
        for e in sorted(entries().values(), key=lambda e: e['start']):
            if in_range(e, a.since, a.until):
                print(f'{e["start"]}  {e["id"]}  {e["summary"]}' + ('  [in Productive]' if e['start'][:10] in done else ''))
    elif a.cmd == 'has':
        known = entries()
        foreign = [i for i in a.ids if i not in known]
        for i in foreign:
            print(f'NOT OURS: {i}')
        sys.exit(1 if foreign else 0)
    elif a.cmd == 'remove':
        known = entries()
        append([{**known[i], 'deleted': now} for i in a.ids if i in known])
        print(f'Marked {sum(i in known for i in a.ids)} event(s) deleted')
    elif a.cmd == 'verify':
        listed = {e['id']: e for e in json.load(open(a.file)).get('events', [])}
        ours = {k: e for k, e in entries().items() if in_range(e, a.since, a.until)}
        missing = [e for k, e in ours.items() if k not in listed]
        print(f'{len(ours)} recorded, {len(ours) - len(missing)} found on the calendar')
        for e in sorted(missing, key=lambda e: e['start']):
            print(f'MISSING: {e["start"]}  {e["id"]}  {e["summary"]}')
        sys.exit(1 if missing else 0)
    elif a.cmd == 'gaps':
        logged = {e['start'][:10] for e in entries().values()}
        print(f'last logged: {max(logged) if logged else "never"}')
        today = date.today()
        days = [today - timedelta(n) for n in range(a.days, -1, -1)]
        print('missing weekdays: ' + (' '.join(d.isoformat() for d in days if d.weekday() < 5 and d.isoformat() not in logged) or 'none'))
        done = imported()
        print('not in Productive yet: ' + (' '.join(d.isoformat() for d in days if d.isoformat() in logged and d.isoformat() not in done) or 'none'))
    elif a.cmd == 'update':
        known = entries()
        if a.id not in known:
            sys.exit(f'NOT OURS: {a.id}')
        e = {**known[a.id], 'updated': now}
        if a.summary:
            e['summary'] = a.summary
        if a.start:
            e['start'] = a.start
        append([e])
        print(f'Updated {a.id}')
    elif a.cmd == 'imported':
        done = imported()
        if a.check:
            print('in Productive: ' + (' '.join(d for d in a.dates if d in done) or 'none'))
            print('not in Productive: ' + (' '.join(d for d in a.dates if d not in done) or 'none'))
        else:
            for d in a.dates:
                if a.undo:
                    done.pop(d, None)
                else:
                    done[d] = now
            os.makedirs(os.path.dirname(IMPORTED), exist_ok=True)
            json.dump(done, open(IMPORTED, 'w'), indent=1)
            print(('Unmarked ' if a.undo else 'Marked in Productive: ') + ' '.join(a.dates))


if __name__ == '__main__':
    main()
