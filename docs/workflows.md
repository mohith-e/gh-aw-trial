# Workflow Reference

Detailed documentation for all agentic workflows in this repo.

## Pipelines

These are end-to-end workflows that chain multiple agents together:

- [PRD-Driven Delivery](workflows/prd-driven-delivery.md) — idea → PRD → stories → implementation → validation
- [Story-Driven Delivery](workflows/story-driven-delivery.md) — idea → opportunity → user activities → stories → implementation → validation
- [Auto-Remediation](workflows/auto-remediation.md) — errors logged → errors triaged → issue created → PR with fix

## Individual Workflows

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| [prd-generation](../workflows/prd-generation.md) | Issue labeled `feature-idea` | Generates a PRD from a feature idea, opens a PR |
| [prd-decomposition](../workflows/prd-decomposition.md) | PRD merged to main | Breaks PRD into epic + story issues with priority labels |
| [story-decomposition](../workflows/story-decomposition.md) | Issue labeled `ready-for-decomposition` | Breaks a story into implementation sub-issues |
| [skill-selection](../workflows/skill-selection.md) | PRD merged to main | Fetches coding skills from `RealPage/ai-coding-toolkit` |
| [mcp-selection](../workflows/mcp-selection.md) | PRD merged to main | Configures MCP servers in the implementation workflow |
| [validation](../workflows/validation.md) | PR labeled `needs-validation` | Validates implementation against PRD acceptance criteria |
| [auto-remediation](../workflows/auto-remediation.md) | Every 2 hours / manual | Queries Elastic for errors, triages, creates issues, assigns Copilot |

> **Not included:** `implementation.md` is project-specific (references your codebase paths, test commands, and tech stack). Use the template in [agentic-workflow-template](https://github.com/RealPage/agentic-workflow-template) as a starting point.

## How Workflows Work

Each workflow is a markdown file with YAML frontmatter that declares the AI engine, safety constraints, and optional MCP server connections. The body contains natural language instructions that the agent follows.

```yaml
---
engine: claude

safe-outputs:
  create-pull-request:
    max: 1
  add-comment:
    max: 3

mcp-servers:         # Optional — external tool access
  elastic:
    url: ${{ vars.ELASTIC_MCP_URL }}
---

# Workflow Title

Instructions the agent follows...
```

Your repo creates thin stubs in `.github/workflows/` that declare triggers and import the shared logic:

```yaml
---
on:
  issues:
    types: [opened, labeled]

imports:
  - RealPage/agentics/workflows/prd-generation.md@v0.1.0
---
```

Running `gh aw compile` resolves imports and generates the GitHub Actions YAML. See the [gh-aw imports reference](https://github.github.com/gh-aw/reference/imports/#remote-repository-imports) for full details.
