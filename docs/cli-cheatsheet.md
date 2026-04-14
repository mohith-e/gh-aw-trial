# gh-aw CLI Cheatsheet

Quick reference for common `gh aw` commands when working with agentic workflows.

## Repository Setup

```bash
# Initialize a repository for agentic workflow authoring
# Adds the GH-AW dispatcher agent, VS Code/MCP dev tooling, and Copilot setup steps
gh aw init

# Add a workflow from a shared library (interactive wizard — walks through setup and creates a PR)
gh aw add-wizard RealPage/agentic-workflows/workflows/<workflow-name>.md@<version>

# Compile a workflow stub into a GitHub Actions lock file
gh aw compile [workflow-name]

# Validate a compiled workflow without running it
gh aw compile --validate

# Update a workflow to a newer version (3-way merge preserves your local changes)
gh aw update <workflow-name>
gh aw update <workflow-name> --ref v0.3.0

# Discard local changes and take the upstream version exactly
gh aw update <workflow-name> --no-merge
```

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
