#!/usr/bin/env python3
"""Per-user settings for timesheet-calendar, kept outside the skill so installs and updates don't touch them.

Usage:
  config.py show              every setting with its value; last line says whether setup is complete
  config.py get KEY
  config.py set KEY VALUE
  config.py guess             suggested values from this machine (git author, timezone)
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
    'workday': ('09:00-18:00', False, 'working hours blocks are planned in'),
    'lunch': ('12:30-13:30', False, 'kept free of blocks'),
    'timezone': (None, False, 'IANA timezone; defaults to this machine'),
}


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
    elif a.cmd == 'get':
        print(get(a.key) or '')
    elif a.cmd == 'set':
        data = load()
        data.setdefault('config', {})[a.key] = a.value
        save(data)
        print(f'{a.key} = {a.value}')


if __name__ == '__main__':
    main()
