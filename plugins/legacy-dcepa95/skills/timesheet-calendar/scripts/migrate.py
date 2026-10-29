#!/usr/bin/env python3
"""Move an install from the old claude-skills marketplace to the dcepa95 marketplace.

Usage:
  migrate.py notice   SessionStart hook: warn that the plugins moved
  migrate.py plan     show what will be removed and installed
  migrate.py run      do it: remove claude-skills, add dcepa95, install default@dcepa95 with the same plugins
"""
import json, os, shutil, subprocess, sys

CONFIG = os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude')
OLD, NEW, SOURCE = 'claude-skills', 'dcepa95', 'dcepa95/claude-skills'
OPTIONS = ['timesheet', 'standup', 'ship', 'ticket', 'design-qa', 'temp-guard']
COMMANDS = (f'claude plugin marketplace remove {OLD}\n'
            f'claude plugin marketplace add {SOURCE}\n'
            f'claude plugin install default@{NEW}')


def load(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def picks():
    installed = load(os.path.join(CONFIG, 'plugins', 'installed_plugins.json'))
    installed = installed.get('plugins', installed)
    names = {k.split('@')[0] for k in installed if k.endswith('@' + OLD)}
    options = (load(os.path.join(CONFIG, 'settings.json')).get('pluginConfigs', {})
               .get(f'dcepa95@{OLD}', {}).get('options', {}))
    names |= {k.replace('_', '-') for k, v in options.items() if v}
    return ['timesheet'] + [p for p in OPTIONS if p in names and p != 'timesheet']


def config_args(keep):
    return [a for p in keep for a in ('--config', f'{p.replace("-", "_")}=true')]


def notice():
    msg = ('Your dcepa95 plugins moved to the "dcepa95" marketplace, and this install (dcepa95@claude-skills) '
           'no longer updates. Run /dcepa95:timesheet-calendar to move now; your timesheet settings stay.')
    print(json.dumps({'systemMessage': msg, 'hookSpecificOutput': {'hookEventName': 'SessionStart',
          'additionalContext': msg + ' The skill dcepa95:timesheet-calendar does the move.'}}))


def plan():
    keep = picks()
    print('Plugins to keep:', ', '.join(keep))
    print('Commands:')
    print(COMMANDS + ' ' + ' '.join(config_args(keep)))


def run():
    claude = shutil.which('claude')
    if not claude:
        sys.exit('claude CLI not found on PATH. Run these yourself:\n' + COMMANDS)
    keep = picks()
    args = config_args(keep)
    for cmd in (['plugin', 'marketplace', 'remove', OLD], ['plugin', 'marketplace', 'add', SOURCE],
                ['plugin', 'install', f'default@{NEW}', *args]):
        r = subprocess.run([claude, *cmd], capture_output=True, text=True)
        print('$ claude ' + ' '.join(cmd))
        print((r.stdout + r.stderr).strip())
        if r.returncode:
            sys.exit(r.returncode)
    print('Done. Restart Claude Code; the next session installs: ' + ', '.join(keep))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'notice':
        try:
            notice()
        except Exception:
            pass
    elif cmd in ('plan', 'run'):
        {'plan': plan, 'run': run}[cmd]()
    else:
        sys.exit(__doc__)
