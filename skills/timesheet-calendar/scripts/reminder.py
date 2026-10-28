#!/usr/bin/env python3
"""Daily macOS reminder to log the timesheet (launchd job showing a dialog with actions).

Usage:
  reminder.py status
  reminder.py terminals                     installed terminal apps, the one running now first
  reminder.py folder [DIR | --reset]        show or set the folder "Do it now" starts Claude in (--reset: ask next time)
  reminder.py terminal [APP] [--ask on|off] show or set the default terminal; --ask off opens it without asking
  reminder.py on [--time HH:MM] [--days weekdays|daily] [--terminal APP] [--cwd DIR]
  reminder.py off
  reminder.py test                          show the dialog now (blocks until answered)
  reminder.py fire                          what launchd runs

The dialog offers "Do it now" (asks which installed terminal to open, default preselected, and starts Claude
with the skill there), "Remind me later…" (15 min to 2 h) and "Skip today". Without a folder set, the first
"Do it now" asks for it.
Choices live in the project registry prefs (reminder, reminder_time, reminder_days, reminder_terminal,
reminder_terminal_ask, reminder_cwd, claude_path).
"""
import argparse, json, os, plistlib, shlex, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projects import load, save

LABEL = 'com.claude.timesheet-reminder'
PLIST = os.path.expanduser(f'~/Library/LaunchAgents/{LABEL}.plist')
DOMAIN = f'gui/{os.getuid()}'
PROMPT = 'fill my time for today'


def skill_command():
    # Plugin skills are namespaced by plugin name; personal skills aren't
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest = os.path.join(skill_dir, '..', '..', '.claude-plugin', 'plugin.json')
    if os.path.exists(manifest):
        return f'/{json.load(open(manifest))["name"]}:timesheet-calendar'
    return '/timesheet-calendar'
# launchd jobs can't read ~/Documents (privacy protection), where the skill may live, so the job runs a copy
BIN = os.path.expanduser('~/.claude/timesheet-calendar/bin')
SNOOZE = {'15 minutes': 15, '30 minutes': 30, '1 hour': 60, '2 hours': 120}
GIVE_UP = 600

# app name -> TERM_PROGRAM value. Only apps that take a command over AppleScript: others would need typed
# keystrokes, which macOS blocks for launchd jobs without an Accessibility grant.
TERMINALS = {'Terminal': 'Apple_Terminal', 'iTerm': 'iTerm.app'}
APP_DIRS = ['/Applications', os.path.expanduser('~/Applications'), '/System/Applications/Utilities']


def launchctl(*args):
    return subprocess.run(['launchctl', *args], capture_output=True, text=True)


def osa(script):
    return subprocess.run(['/usr/bin/osascript', '-e', script], capture_output=True, text=True)


def ascript(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def loaded(label=LABEL):
    return launchctl('print', f'{DOMAIN}/{label}').returncode == 0


def unload(path):
    label = os.path.basename(path)[:-len('.plist')]
    if loaded(label):
        launchctl('bootout', f'{DOMAIN}/{label}')
    if os.path.exists(path):
        os.remove(path)


def prefs():
    return load().get('prefs', {})


def set_prefs(**kv):
    data = load()
    data.setdefault('prefs', {}).update(kv)
    save(data)


def installed_terminals():
    found = [t for t in TERMINALS if any(os.path.exists(f'{d}/{t}.app') for d in APP_DIRS)]
    current = next((t for t, v in TERMINALS.items() if v == os.environ.get('TERM_PROGRAM')), None)
    return sorted(found, key=lambda t: t != current), current


def open_claude(app, cwd, claude, command):
    cmd = f'cd {shlex.quote(cwd)} && {shlex.quote(claude)} {shlex.quote(command + " " + PROMPT)}'
    if app == 'iTerm':
        r = osa(f'tell application "iTerm"\nactivate\nset w to (create window with default profile)\n'
                f'tell current session of w to write text {ascript(cmd)}\nend tell')
    else:
        r = osa(f'tell application "Terminal"\nactivate\ndo script {ascript(cmd)}\nend tell')
    if r.returncode:
        subprocess.run(['pbcopy'], input=cmd, text=True)
        osa(f'display alert "Timesheet reminder couldn\'t open {app}" message '
            f'{ascript(r.stderr.strip() + chr(10) + chr(10) + "The command is on your clipboard.")}')


def ask():
    r = osa('display dialog "Time to log today\'s hours in your timesheet." with title "Timesheet" '
            'buttons {"Skip today", "Remind me later…", "Do it now"} default button "Do it now" '
            f'with icon note giving up after {GIVE_UP}')
    if 'gave up:true' in r.stdout or 'button returned:' not in r.stdout:
        return 'skip'
    return r.stdout.split('button returned:')[1].split(',')[0].strip()


def pick_terminal(last):
    found, _ = installed_terminals()
    if len(found) < 2:
        return found[0] if found else 'Terminal'
    default = last if last in found else found[0]
    r = osa(f'choose from list {{{", ".join(ascript(t) for t in found)}}} with title "Timesheet" '
            f'with prompt "Open Claude in:" default items {{{ascript(default)}}} OK button name "Open"')
    choice = r.stdout.strip()
    return choice if choice in found else None


def pick_folder():
    r = osa('POSIX path of (choose folder with prompt "Which folder should Claude start in? (asked once)" '
            f'default location (POSIX file {ascript(os.path.expanduser("~"))}))')
    return r.stdout.strip().rstrip('/') or None


def fire():
    p = prefs()
    while True:
        choice = ask()
        if choice == 'Do it now':
            last = p.get('reminder_terminal') if p.get('reminder_terminal') in TERMINALS else None
            terminal = last if last and p.get('reminder_terminal_ask') == 'off' else pick_terminal(last)
            cwd = p.get('reminder_cwd') or pick_folder()
            if not terminal or not cwd:
                return
            set_prefs(reminder_terminal=terminal, reminder_cwd=cwd)
            open_claude(terminal, cwd, p.get('claude_path') or shutil.which('claude') or 'claude',
                        p.get('reminder_command', '/timesheet-calendar'))
            return
        if choice != 'Remind me later…':
            return
        items = ', '.join(ascript(s) for s in SNOOZE)
        r = osa(f'choose from list {{{items}}} with title "Timesheet" with prompt "Remind me again in:" '
                'default items {"30 minutes"}')
        later = r.stdout.strip()
        if later not in SNOOZE:
            return
        time.sleep(SNOOZE[later] * 60)


def main():
    if sys.platform != 'darwin':
        sys.exit('Reminders use launchd and only work on macOS.')
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for c in ('status', 'terminals', 'off', 'test', 'fire'):
        sub.add_parser(c)
    on = sub.add_parser('on')
    on.add_argument('--time', default='17:30')
    on.add_argument('--days', choices=['weekdays', 'daily'], default='weekdays')
    on.add_argument('--terminal')
    on.add_argument('--cwd')
    on.add_argument('--command', help='slash command that starts the skill (default: detected)')
    fo = sub.add_parser('folder')
    fo.add_argument('dir', nargs='?')
    fo.add_argument('--reset', action='store_true')
    te = sub.add_parser('terminal')
    te.add_argument('app', nargs='?')
    te.add_argument('--ask', choices=['on', 'off'])
    a = ap.parse_args()

    if a.cmd == 'status':
        p = prefs()
        if loaded():
            print(f'on: {p.get("reminder_days", "weekdays")} at {p.get("reminder_time", "17:30")}')
        else:
            print('off' if 'reminder' in p else 'never set up')
        print(f'folder: {p.get("reminder_cwd", "(asked on first Do it now)")}')
        print(f'command: {p.get("reminder_command", "/timesheet-calendar")} {PROMPT}')
        ask = 'asks each time' if p.get('reminder_terminal_ask') != 'off' else 'opens without asking'
        print(f'terminal: {p.get("reminder_terminal", "(none yet)")}, {ask}')
    elif a.cmd == 'terminals':
        found, current = installed_terminals()
        for t in found:
            print(t + ('  (running Claude now)' if t == current else ''))
    elif a.cmd == 'folder':
        if a.reset:
            data = load()
            data.setdefault('prefs', {}).pop('reminder_cwd', None)
            save(data)
            print('Folder cleared; the next "Do it now" asks for it')
        elif a.dir:
            d = os.path.abspath(os.path.expanduser(a.dir))
            if not os.path.isdir(d):
                sys.exit(f'Not a folder: {d}')
            set_prefs(reminder_cwd=d)
            print(f'Folder: {d}')
        else:
            print(prefs().get('reminder_cwd', '(asked on first Do it now)'))
    elif a.cmd == 'terminal':
        found, _ = installed_terminals()
        if a.app:
            app = next((t for t in found if t.lower() == a.app.lower()), None)
            if not app:
                sys.exit(f'{a.app!r} is not installed; installed: {", ".join(found)}')
            set_prefs(reminder_terminal=app)
        if a.ask:
            set_prefs(reminder_terminal_ask=a.ask)
        p = prefs()
        ask = 'asks each time' if p.get('reminder_terminal_ask') != 'off' else 'opens without asking'
        print(f'Terminal: {p.get("reminder_terminal", "(none yet)")}, {ask}  (installed: {", ".join(found)})')
    elif a.cmd == 'on':
        p = prefs()
        terminal = a.terminal or p.get('reminder_terminal')
        cwd = a.cwd or p.get('reminder_cwd')
        cwd = cwd and os.path.abspath(os.path.expanduser(cwd))
        claude = shutil.which('claude') or p.get('claude_path')
        if not claude:
            sys.exit('`claude` not found on PATH; run this from a shell where `claude` works.')
        h, m = map(int, a.time.split(':'))
        days = range(1, 6) if a.days == 'weekdays' else [None]
        intervals = [{**({'Weekday': d} if d else {}), 'Hour': h, 'Minute': m} for d in days]
        unload(PLIST)
        os.makedirs(BIN, exist_ok=True)
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ('reminder.py', 'projects.py'):
            shutil.copy2(os.path.join(here, name), BIN)
        shutil.rmtree(os.path.join(BIN, 'Timesheet Reminder.app'), ignore_errors=True)
        for name in ('typer.applescript', 'typer-in.txt', 'typer-out.txt'):
            if os.path.exists(os.path.join(BIN, name)):
                os.remove(os.path.join(BIN, name))
        os.makedirs(os.path.dirname(PLIST), exist_ok=True)
        with open(PLIST, 'wb') as f:
            plistlib.dump({'Label': LABEL, 'ProgramArguments': [sys.executable, os.path.join(BIN, 'reminder.py'), 'fire'],
                           'StartCalendarInterval': intervals}, f)
        r = launchctl('bootstrap', DOMAIN, PLIST)
        if r.returncode:
            sys.exit(f'launchctl failed: {r.stderr.strip()}')
        command = a.command or skill_command()
        set_prefs(reminder='on', reminder_time=f'{h:02d}:{m:02d}', reminder_days=a.days, claude_path=claude,
                  reminder_command=command,
                  **({'reminder_terminal': terminal} if terminal else {}), **({'reminder_cwd': cwd} if cwd else {}))
        print(f'Reminder on: {a.days} at {h:02d}:{m:02d} (local time); '
              f'"Do it now" runs {command} in {cwd or "(folder asked on first use)"}')
    elif a.cmd == 'off':
        unload(PLIST)
        set_prefs(reminder='off')
        print('Reminder off')
    elif a.cmd in ('test', 'fire'):
        fire()


if __name__ == '__main__':
    main()
