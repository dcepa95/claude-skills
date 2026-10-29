#!/usr/bin/env python3
"""Compare expected (Figma) and actual (computed style) values, and print a ledger.

Usage:
  compare.py pairs.json [--tol 0.5] [--rem 16]

pairs.json is a list of rows:
  {"region": "Pill label", "property": "font-size", "expected": "11px", "actual": "12px",
   "token": "--text-xs", "severity": "high"}
expected/actual can be px, rem/em (em needs "font_size" on the row), numbers, colours (hex, rgb[a]),
font-weight names or any string. A missing or null side makes the row NOT_PROVEN.
Geometry gets ±tol px; radius, border and font properties must match exactly. Exit code 1 on mismatches.
"""
import json, re, sys

WEIGHTS = {'thin': 100, 'extralight': 200, 'light': 300, 'regular': 400, 'normal': 400, 'book': 400,
           'medium': 500, 'semibold': 600, 'bold': 700, 'extrabold': 800, 'black': 900}
EXACT = ('radius', 'border', 'font', 'line-height', 'letter-spacing', 'outline', 'stroke')


def color(v):
    v = v.strip().lower()
    m = re.fullmatch(r'#([0-9a-f]{3,8})', v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (round(a, 3),)
    m = re.fullmatch(r'rgba?\(([^)]+)\)', v)
    if m:
        parts = [p for p in re.split(r'[,\s/]+', m.group(1)) if p]
        nums = [float(p.rstrip('%')) * (2.55 if p.endswith('%') and i < 3 else 0.01 if p.endswith('%') else 1)
                for i, p in enumerate(parts)]
        return tuple(round(n) for n in nums[:3]) + (round(nums[3] if len(nums) > 3 else 1.0, 3),)
    if v == 'transparent':
        return (0, 0, 0, 0.0)
    return None


def length(v, rem, font_size):
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r'(-?[\d.]+)\s*(px|rem|em)?', v.strip())
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2)
    if unit == 'rem':
        return n * rem
    if unit == 'em':
        return n * font_size if font_size else None
    return n


def hexa(c):
    s = '#' + ''.join(f'{x:02x}' for x in c[:3])
    return s + (f' @{c[3]:g}' if c[3] < 1 else '')


def judge(row, tol, rem):
    prop = row.get('property', '')
    exp, act = row.get('expected'), row.get('actual')
    if exp in (None, '') or act in (None, ''):
        return 'NOT_PROVEN', ''
    if 'weight' in prop:
        e = WEIGHTS.get(str(exp).lower().replace(' ', '').replace('-', ''), exp)
        a = WEIGHTS.get(str(act).lower().replace(' ', '').replace('-', ''), act)
        return ('PASS' if str(e) == str(a) else 'MISMATCH'), ''
    ce, ca = (color(exp), color(act)) if isinstance(exp, str) and isinstance(act, str) else (None, None)
    if ce and ca:
        d = max(abs(x - y) for x, y in zip(ce[:3], ca[:3]))
        da = abs(ce[3] - ca[3])
        ok = d <= 2 and da <= 0.02
        return ('PASS' if ok else 'MISMATCH'), '' if ok else f'{hexa(ce)} vs {hexa(ca)}'
    fs = length(row['font_size'], rem, None) if row.get('font_size') else None
    le, la = length(exp, rem, fs), length(act, rem, fs)
    if le is not None and la is not None:
        allowed = 0.01 if any(k in prop for k in EXACT) else tol
        delta = la - le
        return ('PASS' if abs(delta) <= allowed else 'MISMATCH'), f'{delta:+g}px' if abs(delta) > 0.001 else ''
    norm = lambda s: re.sub(r'["\'\s]+', ' ', str(s)).strip().lower()
    if 'family' in prop:
        return ('PASS' if norm(exp).split(',')[0].strip() == norm(act).split(',')[0].strip() else 'MISMATCH'), ''
    return ('PASS' if norm(exp) == norm(act) else 'MISMATCH'), ''


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        sys.exit(__doc__)
    tol = float(args[args.index('--tol') + 1]) if '--tol' in args else 0.5
    rem = float(args[args.index('--rem') + 1]) if '--rem' in args else 16.0
    rows = json.load(open(args[0]))
    order = {'MISMATCH': 0, 'NOT_PROVEN': 1, 'PASS': 2}
    sev = {'blocker': 0, 'high': 1, 'medium': 2, 'nit': 3}
    judged = []
    for r in rows:
        verdict, delta = judge(r, tol, rem)
        judged.append((verdict, delta, r))
    judged.sort(key=lambda x: (order[x[0]], sev.get(str(x[2].get('severity', 'medium')).lower(), 2)))
    counts = {k: sum(1 for j in judged if j[0] == k) for k in order}
    print(f"{counts['MISMATCH']} mismatch · {counts['NOT_PROVEN']} not proven · {counts['PASS']} pass\n")
    print('| Verdict | Region | Property | Expected | Actual | Delta | Token | Severity |')
    print('|---|---|---|---|---|---|---|---|')
    cell = lambda v: str(v if v is not None else '—').replace('|', '\\|')
    for verdict, delta, r in judged:
        print(f"| {verdict} | {cell(r.get('region'))} | {cell(r.get('property'))} | {cell(r.get('expected'))} | "
              f"{cell(r.get('actual'))} | {delta} | {cell(r.get('token', ''))} | {cell(r.get('severity', ''))} |")
    sys.exit(1 if counts['MISMATCH'] else 0)


if __name__ == '__main__':
    main()
