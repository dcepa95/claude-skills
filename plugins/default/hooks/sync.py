#!/usr/bin/env python3
"""SessionStart hook: install the plugins picked in the default plugin's settings that aren't installed yet.

Only installs. Unticking a plugin never uninstalls it.
"""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude'), 'plugins')


def saved(market):
    """Choices from settings.json, for when an option isn't passed to the hook's environment."""
    try:
        settings = json.load(open(os.path.join(os.path.dirname(PLUGINS_DIR), 'settings.json')))
    except (OSError, ValueError):
        return {}
    return (settings.get('pluginConfigs', {}).get(f'default@{market}') or {}).get('options', {})


def picked(market):
    config = json.load(open(os.path.join(HERE, '..', '.claude-plugin', 'plugin.json')))['userConfig']
    stored = saved(market)
    out = []
    for key, opt in config.items():
        raw = os.environ.get(f'CLAUDE_PLUGIN_OPTION_{key.upper()}')
        if raw not in (None, ''):
            on = raw.strip().lower() in ('true', '1', 'yes', 'on')
        else:
            on = bool(stored.get(key, opt.get('default', False)))
        if on:
            out.append(key.replace('_', '-'))
    return out


def installed():
    try:
        data = json.load(open(os.path.join(PLUGINS_DIR, 'installed_plugins.json')))
    except (OSError, ValueError):
        return {}
    return data.get('plugins', data)


def main():
    plugins = installed()
    root = os.path.dirname(HERE)
    market = next((k.split('@', 1)[1] for k, v in plugins.items()
                   if k.startswith('default@') and any(root.startswith(e.get('installPath', '\0')) for e in v)), 'dcepa95')
    missing = [p for p in picked(market) if f'{p}@{market}' not in plugins]
    if not missing:
        return
    claude = shutil.which('claude')
    if not claude:
        print(json.dumps({'systemMessage': 'Install ' + ', '.join(missing) + f' with: claude plugin install <name>@{market}'}))
        return
    done, failed = [], []
    for p in missing:
        r = subprocess.run([claude, 'plugin', 'install', f'{p}@{market}'], capture_output=True, text=True, timeout=150)
        (done if r.returncode == 0 else failed).append(p)
    parts = []
    if done:
        parts.append('Installed ' + ', '.join(done) + '. Run /reload-plugins or restart Claude Code to use them.')
    if failed:
        parts.append('Could not install ' + ', '.join(failed) + f'; try: claude plugin install <name>@{market}')
    print(json.dumps({'systemMessage': ' '.join(parts)}))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'systemMessage': f'Plugin picker (default@dcepa95) failed: {e}'}))
    sys.exit(0)
