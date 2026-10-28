#!/usr/bin/env python3
"""Compare the installed plugin with the newest commit of its marketplace, and update it.

Usage:
  version.py check     prints nothing when up to date, not installed as a plugin, or offline;
                       otherwise "UPDATE <installed> -> <latest>" and the commits in between
  version.py update    updates the marketplace and the plugin, then refreshes the reminder if it's on
"""
import json, os, subprocess, sys

PLUGINS = os.path.join(os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude'), 'plugins')
HERE = os.path.dirname(os.path.abspath(__file__))


def git(repo, *args, timeout=15):
    try:
        r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def install():
    """(plugin@marketplace, installed commit, marketplace record) for the install these scripts run from."""
    try:
        installed = json.load(open(os.path.join(PLUGINS, 'installed_plugins.json')))
        markets = json.load(open(os.path.join(PLUGINS, 'known_marketplaces.json')))
    except (OSError, ValueError):
        return None
    for key, entries in installed.get('plugins', installed).items():
        for e in entries:
            path = e.get('installPath', '')
            if path and HERE.startswith(path.rstrip('/') + '/'):
                market = markets.get(key.split('@', 1)[1])
                return (key, e.get('gitCommitSha') or e.get('version'), market) if market else None
    return None


def check():
    found = install()
    if not found:
        return
    key, current, market = found
    repo = market['installLocation']
    if market['source'].get('source') != 'directory' and git(repo, 'fetch', '--quiet', '--depth=100', 'origin') is None:
        return
    latest = git(repo, 'rev-parse', 'HEAD' if market['source'].get('source') == 'directory' else 'origin/HEAD')
    if not latest or not current or latest.startswith(current) or current.startswith(latest):
        return
    changes = (git(repo, 'log', '--format=%ad  %s', '--date=format:%d %b', f'{current}..{latest}') or '').splitlines()
    print(f'UPDATE {current[:7]} -> {latest[:7]} ({key}), {len(changes)} changes')
    for line in changes[:8]:
        print('  ' + line)
    if len(changes) > 8:
        print(f'  … and {len(changes) - 8} more')


def update():
    found = install()
    if not found:
        sys.exit('Not installed as a plugin; nothing to update.')
    key, _, _ = found
    for cmd in (['claude', 'plugin', 'marketplace', 'update', key.split('@', 1)[1]], ['claude', 'plugin', 'update', key]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip())
        if r.returncode:
            sys.exit(r.returncode)
    installed = json.load(open(os.path.join(PLUGINS, 'installed_plugins.json')))
    new = installed.get('plugins', installed)[key][0]['installPath']
    reminder = os.path.join(new, 'skills', 'timesheet-calendar', 'scripts', 'reminder.py')
    status = subprocess.run([sys.executable, reminder, 'status'], capture_output=True, text=True).stdout
    if status.startswith('on:'):
        r = subprocess.run([sys.executable, reminder, 'on', '--time', status.split(' at ')[1].split()[0],
                            '--days', status.split()[1]], capture_output=True, text=True)
        print((r.stdout + r.stderr).strip())
    print('Restart Claude Code to use the new version.')


if __name__ == '__main__':
    {'check': check, 'update': update}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: sys.exit(__doc__))()
