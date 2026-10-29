# TEMP/TODO guard

When you ask Claude for something temporary (a hardcoded value, a forced flag, a service turned on locally, debug logs), it marks each change with a `TEMP:` comment. Before Claude runs `git commit`, `git push` or `gh pr create`, a hook checks the lines that would ship:

- **TEMP comments block the command.** Claude has to revert them, or ask you first. "Revert the temporary changes" finds them all.
- **New TODO/FIXME comments get a warning.** The command still runs, and Claude tells you about them.

Only added lines count, so old TODOs don't trigger it, and Markdown files are skipped. It only guards commands Claude runs. Commits you make yourself aren't checked.

To check a branch by hand:

```
python3 <plugin dir>/hooks/markers.py scan --base develop
```

See the [plugin README](../README.md) to install or update.
