# default

Install it to pick several plugins at once:

```
/plugin install default --marketplace dcepa95/claude-skills
```

The install dialog in `/plugin` asks which plugins you want, one switch each. Only Timesheet is on by default:

| Option | Installs |
|---|---|
| Timesheet | [timesheet](../timesheet/README.md) (on by default) |
| Standup | [standup](../standup/README.md), plus timesheet |
| Ship | [ship](../ship/README.md), plus temp-guard |
| Ticket | [ticket](../ticket/README.md) |
| Design QA | [design-qa](../design-qa/README.md) |
| TEMP guard | [temp-guard](../temp-guard/README.md) |

When the next session starts, it installs the ones you switched on, and tells you to run `/reload-plugins` or restart to load them.

To change your choice later, run `/plugin configure default@dcepa95` and start a new session. Switching a plugin off doesn't uninstall it; remove it with `/plugin uninstall <name>@dcepa95`.

From the shell, `claude plugin install` doesn't show the dialog. Pass your choices instead, for example:

```
claude plugin install default@dcepa95 --config standup=true --config ship=true
```

See the [plugin README](../../README.md) for updating.
