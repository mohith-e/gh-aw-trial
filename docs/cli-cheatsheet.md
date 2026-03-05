# gh-aw CLI Cheatsheet

Quick reference for common `gh aw` commands when working with agentic workflows.

## Managing Workflows

```bash
# Pause a workflow (stops it from triggering)
gh aw disable <workflow>

# Resume a paused workflow
gh aw enable <workflow>
```

## Debugging & Metrics

```bash
# See status of all workflows in your repo
gh aw status

# View logs for recent workflow runs
gh aw logs

# View the full audit trail for a specific run
gh aw audit <runnerid>
```
