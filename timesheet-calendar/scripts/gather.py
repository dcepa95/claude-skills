#!/usr/bin/env python3
"""Collect timestamped work evidence (git commits, reflog, Claude Code prompts) per day.

Usage:
  gather.py discover <parent-dir> [--since YYYY-MM-DD]
  gather.py collect --since YYYY-MM-DD --until YYYY-MM-DD [--author REGEX] [--skip-session ID] DIR [DIR ...]
"""
import argparse, glob, json, os, re, subprocess, sys
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get('TIMESHEET_TZ', 'Europe/Amsterdam'))
PROJECTS = os.path.expanduser('~/.claude/projects')
DEFAULT_AUTHOR = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()


def claude_dir(path):
    return os.path.join(PROJECTS, re.sub(r'[^A-Za-z0-9]', '-', os.path.abspath(path)))


def iso(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(TZ)


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def is_repo(path):
    return os.path.exists(os.path.join(path, '.git'))


def author_args(author):
    # Extended regex, so 'a|b' and 'a\|b' both mean either name
    return ['-E', f'--author={author.replace(chr(92) + "|", "|")}']


def discover(parent, since, author):
    rows = []
    for d in sorted(os.listdir(parent)):
        p = os.path.join(parent, d)
        if not os.path.isdir(p):
            continue
        repo = is_repo(p)
        cdir = claude_dir(p)
        sessions = [f for f in glob.glob(os.path.join(cdir, '*.jsonl')) if os.path.getmtime(f) >= since.timestamp()]
        mine = git(p, 'log', '--all', *author_args(author), f'--since={since:%Y-%m-%d} 00:00', '--format=%ad', '--date=short').split() if repo else []
        if mine or sessions:
            rows.append((d, len(mine), max(mine) if mine else '-', len(sessions)))
    print(f'Activity by {author!r} since {since:%Y-%m-%d}')
    print(f'{"folder":45} {"commits":8} {"last":12} claude sessions')
    for r in rows:
        print(f'{r[0]:45} {r[1]:<8} {r[2]:12} {r[3]}')


def gh(*args):
    try:
        r = subprocess.run(['gh', *args], capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def github_repo(d):
    m = re.search(r'github\.com[:/](.+?)(?:\.git)?$', git(d, 'remote', 'get-url', 'origin').strip())
    return m.group(1) if m else None


def github(repos, since, add):
    """Authored PRs (opened/merged) and reviews by the user. Returns {branch: 'PR #n title'}."""
    login = (gh('api', 'user', '-q', '.login') or '').strip()
    if not login:
        print('NOTE: GitHub evidence skipped (gh not installed or not logged in: `brew install gh && gh auth login`).')
        return {}
    branches = {}
    for repo in sorted(repos):
        short = repo.split('/')[-1]
        prs = json.loads(gh('pr', 'list', '-R', repo, '--author', '@me', '--state', 'all', '--limit', '100',
                            '--search', f'updated:>={since:%Y-%m-%d}',
                            '--json', 'number,title,headRefName,createdAt,mergedAt') or '[]')
        for p in prs:
            branches[p['headRefName']] = f'#{p["number"]} {p["title"]}'
            add(iso(p['createdAt']), f'{short} github', f'opened PR #{p["number"]} {p["title"]} ({p["headRefName"]})')
            if p.get('mergedAt'):
                add(iso(p['mergedAt']), f'{short} github', f'merged PR #{p["number"]} {p["title"]}')
        reviewed = json.loads(gh('search', 'prs', '--repo', repo, '--reviewed-by', '@me', '--updated', f'>={since:%Y-%m-%d}',
                                 '--limit', '100', '--json', 'number,title') or '[]')
        for p in reviewed:
            reviews = json.loads(gh('api', f'repos/{repo}/pulls/{p["number"]}/reviews', '--paginate') or '[]')
            for r in reviews:
                if (r.get('user') or {}).get('login') == login and r.get('submitted_at'):
                    add(iso(r['submitted_at']), f'{short} github', f'reviewed PR #{p["number"]} {p["title"]} ({r["state"].lower()})')
    return branches


def collect(dirs, since, until, author, skip, use_github):
    events = defaultdict(list)
    seen = set()

    def add(t, src, text):
        if since <= t < until:
            events[t.date()].append((t, src, ' '.join(text.split())[:220]))

    repos = set()
    for d in dirs:
        name = os.path.basename(os.path.abspath(d))
        if is_repo(d):
            repos.add(github_repo(d))
            out = git(d, 'log', '--all', *author_args(author), f'--since={since:%Y-%m-%d} 00:00', '--date=iso-strict', '--format=%H\t%ad\t%s\t%D')
            for line in out.splitlines():
                h, ad, subj, refs = (line.split('\t') + ['', ''])[:4]
                if h in seen:
                    continue
                seen.add(h)
                add(iso(ad), f'{name} commit', f'{subj} [{refs}]' if refs else subj)
            out = git(d, 'reflog', '--date=iso-strict', '--format=%H\t%gd\t%gs')
            for line in out.splitlines():
                m = re.match(r'(\w+)\tHEAD@\{(.+?)\}\t(.*)', line)
                if m and not (m.group(3).startswith('commit') and m.group(1) in seen):
                    add(iso(m.group(2)), f'{name} reflog', m.group(3))
        for f in glob.glob(os.path.join(claude_dir(d), '*.jsonl')):
            if skip and skip in f:
                continue
            sid = os.path.basename(f)[:8]
            for line in open(f, errors='ignore'):
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get('type') != 'user' or o.get('isMeta') or o.get('isSidechain') or not o.get('timestamp'):
                    continue
                c = o.get('message', {}).get('content')
                if isinstance(c, list):
                    c = ' '.join(x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text')
                if not isinstance(c, str) or not c.strip() or c.lstrip().startswith('<'):
                    continue
                t = iso(o['timestamp'])
                add(t, f'{name} claude:{sid} [{o.get("gitBranch", "")}]', c)

    branches = github(repos - {None}, since, add) if use_github else {}
    if branches:
        print('Branch → PR')
        for b, title in sorted(branches.items()):
            print(f'  {b}  →  {title}')
    for day in sorted(events):
        print(f'\n=== {day:%a %d %b %Y}' + ('  (WEEKEND)' if day.weekday() >= 5 else ''))
        for t, src, text in sorted(events[day]):
            print(f'  {t:%H:%M}  {src}  {text}')
    if not events:
        print('No activity found in range.')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('discover')
    d.add_argument('parent')
    d.add_argument('--since')
    d.add_argument('--author', default=DEFAULT_AUTHOR)
    c = sub.add_parser('collect')
    c.add_argument('dirs', nargs='+')
    c.add_argument('--since', required=True)
    c.add_argument('--until', required=True, help='inclusive end date')
    c.add_argument('--author', default=DEFAULT_AUTHOR, help='git --author regex, e.g. "name\\|Full Name"')
    c.add_argument('--skip-session', help='session id to ignore (the current one)')
    c.add_argument('--no-github', action='store_true', help='skip PR titles and reviews from GitHub')
    a = ap.parse_args()
    day = lambda s: datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=TZ)
    if a.cmd == 'discover':
        discover(os.path.expanduser(a.parent), day(a.since) if a.since else datetime.now(TZ) - timedelta(days=31), a.author)
    else:
        collect([os.path.expanduser(x) for x in a.dirs], day(a.since), day(a.until) + timedelta(days=1), a.author, a.skip_session, not a.no_github)


if __name__ == '__main__':
    sys.exit(main())
