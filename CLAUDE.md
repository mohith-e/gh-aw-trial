# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A library of reusable GitHub Agentic Workflows (gh-aw) for automating the software development lifecycle with Claude-powered agents. Consumer repos import these workflows via remote imports — no file copying needed.

This repo contains **no application code, no build system, no tests**. It is entirely markdown-based workflow definitions and documentation.

## Repository Structure

- `workflows/` — The canonical workflow definitions imported by consumer repos. **This is the primary source of truth.**
- `examples/` — Example consumer stubs showing the YAML frontmatter (triggers, permissions, imports) that consumer repos use in `.github/workflows/`.
- `docs/workflows.md` — Detailed workflow reference with pipeline diagrams.
- `docs/prds/templates/` — PRD template used by the `prd-generation` workflow.
- `docs/demos/` — Demo scripts and presentation materials.

## Workflow Anatomy

Each workflow definition in `workflows/` is a markdown file with YAML frontmatter:

```yaml
---
engine: claude
safe-outputs:        # Allowed side effects with optional limits
  create-pull-request:
    max: 1
  add-comment:
    max: 3
mcp-servers:         # Optional external tool access (e.g., Elastic)
  elastic:
    url: ${{ vars.ELASTIC_MCP_URL }}
---
```

The markdown body contains natural language instructions that Claude agents follow when the workflow triggers.

## Workflows

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| `prd-generation` | Issue labeled `feature-idea` | Generates a PRD from a feature idea, opens a PR |
| `prd-decomposition` | PRD merged to main | Breaks PRD into epic + story issues with priority labels |
| `story-decomposition` | Issue labeled `ready-for-decomposition` | Breaks a story into implementation sub-issues |
| `skill-selection` | PRD merged to main | Fetches coding skills from `RealPage/ai-coding-toolkit` |
| `mcp-selection` | PRD merged to main | Configures MCP servers in the implementation workflow |
| `validation` | PR labeled `needs-validation` | Validates implementation against PRD acceptance criteria |
| `auto-remediation` | Hourly schedule / manual | Queries Elastic for errors, triages, creates issues, opens fix PRs |

## How Consumer Repos Use This

Consumer repos create thin stubs in `.github/workflows/` that declare triggers/permissions and import shared logic:

```yaml
---
on:
  issues:
    types: [opened, labeled]
imports:
  - RealPage/agentics/workflows/prd-generation.md@v0.1.0
---
```

Then run `gh aw compile` to resolve imports and generate final workflow files.

## Contributing

1. Edit the workflow under `workflows/`
2. Test by pointing a consumer stub at your branch: `@my-branch`
3. Open a PR — once merged and tagged, consumers bump their version ref

## Versioning

Uses semver tags (e.g., `v0.1.0`). Consumer repos pin to a version. Bump tags after merging changes:
- Patch: bug fixes to instructions
- Minor: new workflows or non-breaking enhancements
- Major: breaking changes

## Key Conventions

- Workflows assume consumer repos have a `CLAUDE.md` describing their project context and a PRD template at `docs/prds/templates/prd-template.md`.
- The `auto-remediation` workflow requires `SERVICE_NAME` variable, `ELASTIC_MCP_URL` variable, and `ELASTIC_MCP_API_KEY` secret in the consumer repo.
- `implementation.md` is intentionally NOT shared — it is project-specific and lives only in consumer repos.
