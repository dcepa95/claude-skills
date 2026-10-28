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

# app name -> TERM_PROGRAM value
TERMINALS = {'Terminal': 'Apple_Terminal', 'iTerm': 'iTerm.app', 'Hyper': 'Hyper', 'Ghostty': 'ghostty',
             'Warp': 'WarpTerminal', 'WezTerm': 'WezTerm', 'Alacritty': 'alacritty', 'kitty': 'kitty'}
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
    if app == 'Terminal':
        r = osa(f'tell application "Terminal"\nactivate\ndo script {ascript(cmd)}\nend tell')
    elif app == 'iTerm':
        r = osa(f'tell application "iTerm"\nactivate\nset w to (create window with default profile)\n'
                f'tell current session of w to write text {ascript(cmd)}\nend tell')
    else:
        r = type_in_new_window(app, cmd)
    if r.returncode:
        subprocess.run(['pbcopy'], input=cmd, text=True)
        if 'not allowed assistive access' in r.stderr:
            why = f'Allow "{TYPER_NAME}" in Privacy & Security → Accessibility (opening it now), then use Do it now again.'
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
        else:
            why = r.stderr.strip()
        osa(f'display alert "Timesheet reminder couldn\'t open {app}" message '
            f'{ascript(why + chr(10) + chr(10) + "Nothing was typed. The command is on your clipboard.")}')


# Apps without a scripting API (Hyper, Ghostty, ...) get a new window with the command typed in. macOS only lets
# an app with Accessibility permission type, and launchd jobs and osascript have none, so the typing happens
# inside a small applet the user allows once. Rebuilding it resets that permission, so it only changes with TYPER.
# Only types once a new window is confirmed in front, so keystrokes never land in an existing session.
TYPER_NAME = 'Timesheet Reminder'
TYPER_APP = os.path.join(BIN, f'{TYPER_NAME}.app')
TYPER = '''set bin to "%s"
set args to paragraphs of (read POSIX file (bin & "/typer-in.txt") as «class utf8»)
set appName to item 1 of args
set cmd to item 2 of args
try
	set wasRunning to application appName is running
	tell application appName to activate
	tell application "System Events" to tell process appName
		repeat 40 times
			if frontmost then exit repeat
			delay 0.25
		end repeat
		if not frontmost then error appName & " didn't come to the front."
		set n to 0
		if wasRunning then
			set n to count of windows
			keystroke "n" using command down
		end if
		repeat 40 times
			if (count of windows) > n then exit repeat
			delay 0.25
		end repeat
		if (count of windows) <= n then error "No new " & appName & " window appeared."
		delay 1.5
		if not frontmost then error appName & " lost focus before typing."
		keystroke cmd
		key code 36
	end tell
	set msg to ""
on error e
	set msg to e
end try
do shell script "printf %%s " & quoted form of msg & " > " & quoted form of (bin & "/typer-out.txt")
'''


def install_typer():
    src, path = TYPER % BIN, os.path.join(BIN, 'typer.applescript')
    if os.path.exists(TYPER_APP) and os.path.exists(path) and open(path).read() == src:
        return
    shutil.rmtree(TYPER_APP, ignore_errors=True)
    with open(path, 'w') as f:
        f.write(src)
    subprocess.run(['osacompile', '-o', TYPER_APP, path], check=True)
    # No Dock icon; re-sign since editing Info.plist breaks the applet's signature
    subprocess.run(['plutil', '-insert', 'LSUIElement', '-bool', 'true', os.path.join(TYPER_APP, 'Contents', 'Info.plist')], check=True)
    subprocess.run(['codesign', '-f', '-s', '-', TYPER_APP], capture_output=True, check=True)


def type_in_new_window(app, cmd):
    if not os.path.exists(TYPER_APP):
        return subprocess.CompletedProcess([], 1, '', 'Run `reminder.py on` once to install the typing helper.')
    out = os.path.join(BIN, 'typer-out.txt')
    with open(os.path.join(BIN, 'typer-in.txt'), 'w') as f:
        f.write(f'{app}\n{cmd}\n')
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['open', '-W', '-n', TYPER_APP])
    err = open(out).read().strip() if os.path.exists(out) else f"{TYPER_NAME} didn't run."
    return subprocess.CompletedProcess([], 1 if err else 0, '', err)


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
            last = p.get('reminder_terminal')
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
        install_typer()
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
