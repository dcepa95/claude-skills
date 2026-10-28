#!/usr/bin/env python3
"""Persistent project registry for timesheet-calendar.

Usage:
  projects.py colors                      show the Google Calendar event palette
  projects.py list                        show remembered projects
  projects.py match DIR [DIR ...]         map folders to projects (UNKNOWN if none)
  projects.py set KEY [--short S] [--project P] [--service S] [--color C] [--folders GLOB,GLOB] [--jira URL]
  projects.py remove KEY
  projects.py pref NAME [VALUE]           read or remember a preference (e.g. title_source pr|branch)

--project may contain {YYYY} and {MM}; they're filled from each block's date.
--color takes an id (1-11) or a name (e.g. flamingo).
--jira is a ticket link with {n} for the number, e.g. https://x.atlassian.net/browse/ABC-{n}; '' removes it.
"""
import argparse, fnmatch, json, os, sys
from datetime import date

STORE = os.path.expanduser(os.environ.get('TIMESHEET_PROJECTS', '~/.claude/timesheet-calendar/projects.json'))

# Google Calendar event colours: id -> (name, emoji, hex)
COLORS = {
    '1': ('Lavender', '🟪', '#7986cb'), '2': ('Sage', '🟩', '#33b679'), '3': ('Grape', '🟣', '#8e24aa'),
    '4': ('Flamingo', '🩷', '#e67c73'), '5': ('Banana', '🟨', '#f6bf26'), '6': ('Tangerine', '🟧', '#f4511e'),
    '7': ('Peacock', '🔵', '#039be5'), '8': ('Graphite', '⬛', '#616161'), '9': ('Blueberry', '🟦', '#3f51b5'),
    '10': ('Basil', '🟢', '#0b8043'), '11': ('Tomato', '🟥', '#d50000'),
}


def swatch(cid):
    name, emoji, hx = COLORS[cid]
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return f'\033[48;2;{r};{g};{b}m    \033[0m {emoji} {cid:>2} {name}'


def color_id(c):
    if c in COLORS:
        return c
    for k, (name, *_) in COLORS.items():
        if name.lower() == c.lower():
            return k
    sys.exit(f'Unknown colour {c!r}; run `projects.py colors`')


def load():
    if os.path.exists(STORE):
        return json.load(open(STORE))
    return {'projects': {}}


def save(data):
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    json.dump(data, open(STORE, 'w'), indent=2, ensure_ascii=False)


def resolve(p, day):
    """Project fields for a block on `day` (YYYY-MM-DD)."""
    y, m = day[:4], day[5:7]
    return {**p, 'project': p['project'].replace('{YYYY}', y).replace('{MM}', m)}


def match(data, folder):
    name = os.path.basename(os.path.abspath(os.path.expanduser(folder)))
    for key, p in data['projects'].items():
        if any(fnmatch.fnmatch(name, g) for g in p.get('folders', [])):
            return key
    return None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('colors')
    sub.add_parser('list')
    m = sub.add_parser('match')
    m.add_argument('dirs', nargs='+')
    s = sub.add_parser('set')
    s.add_argument('key')
    for f in ('short', 'project', 'service', 'color', 'folders', 'jira'):
        s.add_argument(f'--{f}')
    r = sub.add_parser('remove')
    r.add_argument('key')
    pf = sub.add_parser('pref')
    pf.add_argument('name')
    pf.add_argument('value', nargs='?')
    a = ap.parse_args()
    data = load()

    if a.cmd == 'colors':
        used = {p['color']: k for k, p in data['projects'].items()}
        for cid in COLORS:
            print(swatch(cid) + (f'   (used by {used[cid]})' if cid in used else ''))
    elif a.cmd == 'list':
        if not data['projects']:
            print(f'No projects yet ({STORE})')
        for k, p in data['projects'].items():
            print(f'{swatch(p["color"])}  [{k}] {p["short"]}  ·  {p["project"]} / {p["service"]}  ·  folders: {", ".join(p.get("folders", []))}  ·  last used {p.get("last_used", "-")}')
    elif a.cmd == 'match':
        for d in a.dirs:
            k = match(data, d)
            print(f'{d}\t{k or "UNKNOWN"}' + (f'\t{data["projects"][k]["short"]}' if k else ''))
    elif a.cmd == 'set':
        p = data['projects'].get(a.key, {})
        new = a.key not in data['projects']
        if new and not all((a.short, a.project, a.service, a.color)):
            sys.exit('New project needs --short, --project, --service and --color')
        for f in ('short', 'project', 'service'):
            if getattr(a, f):
                p[f] = getattr(a, f)
        if a.jira is not None:
            p['jira'] = a.jira
        if a.color:
            p['color'] = color_id(a.color)
        if a.folders:
            p['folders'] = sorted(set(p.get('folders', [])) | {g.strip() for g in a.folders.split(',') if g.strip()})
        p['last_used'] = date.today().isoformat()
        data['projects'][a.key] = p
        save(data)
        print(('Added ' if new else 'Updated ') + f'[{a.key}] ' + swatch(p['color']))
    elif a.cmd == 'remove':
        data['projects'].pop(a.key, None)
        save(data)
        print(f'Removed {a.key}')
    elif a.cmd == 'pref':
        prefs = data.setdefault('prefs', {})
        if a.value is None:
            print(prefs.get(a.name, ''))
        else:
            prefs[a.name] = a.value
            save(data)
            print(f'{a.name} = {a.value}')


if __name__ == '__main__':
    main()
