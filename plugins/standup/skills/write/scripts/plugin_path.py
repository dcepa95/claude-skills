#!/usr/bin/env python3
"""Print the install directory of another plugin from this plugin's marketplace.

Usage: plugin_path.py <plugin name>
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGINS = os.path.join(os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude'), 'plugins')


def own_root():
    d = HERE
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.claude-plugin', 'plugin.json')):
            return d
        d = os.path.dirname(d)
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    name = sys.argv[1]
    root = own_root()
    # A marketplace checkout loaded in place keeps plugins side by side
    if root:
        sibling = os.path.join(os.path.dirname(root), name)
        if os.path.exists(os.path.join(sibling, '.claude-plugin', 'plugin.json')):
            print(sibling)
            return
    try:
        installed = json.load(open(os.path.join(PLUGINS, 'installed_plugins.json')))
    except (OSError, ValueError):
        installed = {}
    entries = installed.get('plugins', installed)
    market = None
    for key, items in entries.items():
        if root and any(root.startswith(e.get('installPath', '').rstrip('/') + '/') or root == e.get('installPath') for e in items):
            market = key.split('@', 1)[1]
    for key, items in entries.items():
        n, _, m = key.partition('@')
        if n == name and (market is None or m == market) and items and os.path.isdir(items[0].get('installPath', '')):
            print(items[0]['installPath'])
            return
    sys.exit(f'Plugin "{name}" is not installed. Install it with: claude plugin install {name}@{market or "claude-skills"}')


if __name__ == '__main__':
    main()
