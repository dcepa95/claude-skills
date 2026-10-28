#!/usr/bin/env python3
"""Per-user settings for timesheet-calendar, kept outside the skill so installs and updates don't touch them.

Usage:
  config.py show              every setting with its value; last line says whether setup is complete
  config.py get KEY
  config.py set KEY VALUE
  config.py guess             suggested values from this machine (git author, timezone, folders full of git repos)
"""
import argparse, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projects import load, save


def system_timezone():
    try:
        return os.path.realpath('/etc/localtime').split('zoneinfo/')[1]
    except IndexError:
        return 'UTC'


# key -> (default, required, description)
KEYS = {
    'target_calendar': (None, True, 'private calendar the blocks go in (Productive reads it)'),
    'meetings_calendar': ('primary', False, 'calendar with your meetings, read only'),
    'holiday_calendar': ('', False, 'public-holiday calendar, read only; empty for none'),
    'author': (None, True, 'git author regex matching your commits, e.g. "jane|Jane Doe"'),
    'projects_dir': (None, True, 'folder that holds all your project checkouts'),
    'workday': ('09:00-18:00', False, 'working hours blocks are planned in'),
    'lunch': ('12:30-13:30', False, 'kept free of blocks'),
    'timezone': (None, False, 'IANA timezone; defaults to this machine'),
}


def repo_count(d):
    try:
        return sum(os.path.exists(os.path.join(d, c, '.git')) for c in os.listdir(d))
    except OSError:
        return 0


def project_dirs():
    """Folders near home with the most git checkouts directly inside, most first."""
    home = os.path.expanduser('~')
    seen = set()
    for top in [home] + [os.path.join(home, x) for x in ('Desktop', 'Documents', 'Developer', 'Projects', 'projects', 'code', 'Code', 'dev', 'src', 'repos', 'work', 'Sites')]:
        if not os.path.isdir(top):
            continue
        seen.add(top)
        for c in os.listdir(top):
            if not c.startswith('.') and os.path.isdir(os.path.join(top, c)):
                seen.add(os.path.join(top, c))
    counts = [(d, repo_count(d)) for d in seen]
    return sorted([x for x in counts if x[1] >= 2], key=lambda x: -x[1])


def get(key):
    default = system_timezone() if key == 'timezone' else KEYS[key][0]
    return load().get('config', {}).get(key) or default


def git_config(name):
    r = subprocess.run(['git', 'config', '--global', name], capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('show')
    sub.add_parser('guess')
    g = sub.add_parser('get')
    g.add_argument('key', choices=KEYS)
    s = sub.add_parser('set')
    s.add_argument('key', choices=KEYS)
    s.add_argument('value')
    a = ap.parse_args()

    if a.cmd == 'show':
        missing = []
        for k, (_, required, desc) in KEYS.items():
            v = get(k)
            if required and not v:
                missing.append(k)
            print(f'{k} = {v if v else "(MISSING)" if required else "(none)"}    # {desc}')
        print('setup: complete' if not missing else f'setup: needed (missing: {", ".join(missing)})')
    elif a.cmd == 'guess':
        names = [n for n in (git_config('user.name'), git_config('user.email').split('@')[0]) if n]
        print(f'author = {"|".join(dict.fromkeys(names))}')
        print(f'timezone = {system_timezone()}')
        for d, n in project_dirs()[:3]:
            print(f'projects_dir candidate = {d.replace(os.path.expanduser("~"), "~", 1)}  ({n} git repos)')
    elif a.cmd == 'get':
        print(get(a.key) or '')
    elif a.cmd == 'set':
        if a.key == 'projects_dir':
            a.value = os.path.abspath(os.path.expanduser(a.value))
            if not os.path.isdir(a.value):
                sys.exit(f'Not a folder: {a.value}')
        data = load()
        data.setdefault('config', {})[a.key] = a.value
        save(data)
        print(f'{a.key} = {a.value}')


if __name__ == '__main__':
    main()
