#!/usr/bin/env python3
"""Find TEMP and TODO/FIXME comments in the lines a change adds.

Usage:
  markers.py scan [--repo DIR] [--base REF | --staged]
                  lines added on this branch since REF (default: the remote default branch), or staged;
                  prints "TEMP <file>:<line>: <text>" / "TODO <file>:<line>: <text>", nothing when clean
  markers.py hook     PreToolUse hook: blocks git commit/push and gh pr create while TEMP markers are in
                      what they'd ship, and warns about new TODOs
  markers.py context  SessionStart hook: tells Claude to mark temporary changes with TEMP
"""
import json, os, re, shlex, subprocess, sys

OPENER = r'(?:/{2,}|/\*+|#+|<!--|\{/\*|^\s*\*)\s*'
TEMP_RE = re.compile(OPENER + r'TEMP\b')
TODO_RE = re.compile(OPENER + r'(?:TODO|FIXME)\b')
SKIP_EXT = ('.md', '.txt', '.lock')

CONTEXT = (
    'Temporary changes: when the user asks for something temporary (debug logs, hardcoded values, '
    'forced flags, a service enabled only locally, anything they will want reverted), mark every changed '
    'spot with a comment that starts with "TEMP:" and a short reason, in the file\'s comment syntax. '
    'This applies even where comments are otherwise kept to a minimum. A hook blocks git commit, git push '
    'and gh pr create while TEMP comments are in the changes, and warns about new TODO/FIXME comments. '
    'When the user asks to revert the temporary changes, search for the TEMP: comments and undo each change.'
)


def git(repo, *args):
    try:
        r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def default_base(repo):
    head = (git(repo, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD') or '').strip()
    if head:
        return head
    for ref in ('origin/develop', 'origin/main', 'origin/master', 'develop', 'main', 'master'):
        if git(repo, 'rev-parse', '--verify', '--quiet', ref) is not None:
            return ref
    return None


def resolve(repo, base):
    for ref in (f'origin/{base}', base):
        if git(repo, 'rev-parse', '--verify', '--quiet', ref) is not None:
            return ref
    return base


def added_lines(diff):
    path, line = None, 0
    for raw in (diff or '').splitlines():
        if raw.startswith('+++ '):
            path = raw[6:] if raw.startswith('+++ b/') else None
        elif raw.startswith('@@'):
            m = re.match(r'@@ -\S+ \+(\d+)', raw)
            line = int(m.group(1)) if m else 0
        elif raw.startswith('+') and path:
            yield path, line, raw[1:]
            line += 1


def untracked_lines(repo):
    for path in (git(repo, 'ls-files', '--others', '--exclude-standard') or '').splitlines():
        try:
            with open(os.path.join(repo, path), errors='replace') as f:
                for n, text in enumerate(f, 1):
                    yield path, n, text.rstrip('\n')
        except OSError:
            continue


def find(lines):
    found = []
    for path, n, text in lines:
        if path.endswith(SKIP_EXT):
            continue
        kind = 'TEMP' if TEMP_RE.search(text) else 'TODO' if TODO_RE.search(text) else None
        if kind:
            found.append((kind, f'{path}:{n}: {text.strip()[:160]}'))
    return found


def branch_lines(repo, base):
    return added_lines(git(repo, 'diff', '-U0', '--no-color', f'{base}...HEAD'))


def scan(argv):
    repo, base, staged = os.getcwd(), None, False
    it = iter(argv)
    for a in it:
        if a == '--repo':
            repo = next(it)
        elif a == '--base':
            base = next(it)
        elif a == '--staged':
            staged = True
    if staged:
        lines = added_lines(git(repo, 'diff', '-U0', '--no-color', '--cached'))
    else:
        base = resolve(repo, base) if base else default_base(repo)
        if not base:
            sys.exit('no base branch found; pass --base')
        lines = branch_lines(repo, base)
    for kind, where in find(lines):
        print(kind, where)


def segments(command, cwd):
    """(dir, argv) for each simple command, following cd."""
    for part in re.split(r'&&|\|\||;|\n|\|', command):
        try:
            argv = shlex.split(part)
        except ValueError:
            argv = part.split()
        while argv and re.match(r'^\w+=', argv[0]):
            argv = argv[1:]
        if not argv:
            continue
        if argv[0] == 'cd' and len(argv) > 1:
            cwd = os.path.join(cwd, os.path.expanduser(argv[1]))
            continue
        yield cwd, argv


def git_subcommand(argv):
    """(-C dir, subcommand, rest) of a git argv."""
    i, where = 1, None
    while i < len(argv) and argv[i].startswith('-'):
        if argv[i] in ('-C', '-c') and i + 1 < len(argv):
            if argv[i] == '-C':
                where = argv[i + 1]
            i += 2
        else:
            i += 1
    return where, (argv[i] if i < len(argv) else None), argv[i + 1:]


def flag(rest, short, long):
    return any(a == long or (a.startswith('-') and not a.startswith('--') and short in a[1:]) for a in rest)


def option(rest, *names):
    for i, a in enumerate(rest):
        if a in names and i + 1 < len(rest):
            return rest[i + 1]
        for n in names:
            if n.startswith('--') and a.startswith(n + '='):
                return a.split('=', 1)[1]
    return None


def checks(command, cwd):
    """(action, lines) for each git commit/push or gh pr create in the command."""
    added_first = False
    for base_dir, argv in segments(command, cwd):
        if argv[0] == 'git':
            where, sub, rest = git_subcommand(argv)
            repo = os.path.join(base_dir, os.path.expanduser(where)) if where else base_dir
            if sub == 'add':
                added_first = True
            elif sub == 'commit':
                if added_first or flag(rest, 'a', '--all'):
                    diff = git(repo, 'diff', '-U0', '--no-color', 'HEAD')
                    if diff is None:
                        diff = git(repo, 'diff', '-U0', '--no-color', '--cached')
                    lines = list(added_lines(diff)) + (list(untracked_lines(repo)) if added_first else [])
                else:
                    lines = list(added_lines(git(repo, 'diff', '-U0', '--no-color', '--cached')))
                yield 'commit', lines
            elif sub == 'push':
                upstream = git(repo, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
                base = upstream.strip() if upstream else default_base(repo)
                if base:
                    yield 'push', list(branch_lines(repo, base))
        elif argv[0] == 'gh' and argv[1:3] == ['pr', 'create']:
            rest = argv[3:]
            base = option(rest, '--base', '-B')
            base = resolve(base_dir, base) if base else default_base(base_dir)
            if base:
                yield 'open a PR with', list(branch_lines(base_dir, base))


def hook():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    command = (data.get('tool_input') or {}).get('command') or ''
    if not re.search(r'\bgit\b.*\b(commit|push)\b|\bgh\s+pr\s+create\b', command, re.S):
        return
    temps, todos, actions = [], [], []
    for action, lines in checks(command, data.get('cwd') or os.getcwd()):
        actions.append(action)
        for kind, where in find(lines):
            (temps if kind == 'TEMP' else todos).append(where)
    temps, todos = list(dict.fromkeys(temps)), list(dict.fromkeys(todos))
    what = ' / '.join(dict.fromkeys(actions))
    if temps:
        reason = (f'Blocked: TEMP comments in what this would {what}:\n' + '\n'.join(temps) +
                  '\nThey mark temporary changes. Revert them first, or ask the user; only if they '
                  'say to keep one, remove its TEMP comment.')
        if todos:
            reason += '\nAlso new TODO/FIXME comments:\n' + '\n'.join(todos)
        out = {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                      'permissionDecisionReason': reason}}
    elif todos:
        note = f'New TODO/FIXME comments in what this will {what}:\n' + '\n'.join(todos)
        out = {'systemMessage': note,
               'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                      'additionalContext': note + '\nMention them to the user.'}}
    else:
        return
    print(json.dumps(out))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'scan':
        scan(sys.argv[2:])
    elif cmd == 'hook':
        try:
            hook()
        except Exception:
            pass
    elif cmd == 'context':
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': CONTEXT}}))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
