# Workflow Reference

Detailed documentation for all agentic workflows in this repo.

## Available Workflows

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| [prd-generation](../workflows/prd-generation.md) | Issue labeled `feature-idea` | Generates a PRD from a feature idea, opens a PR |
| [decomposition](../workflows/decomposition.md) | PRD merged to main | Breaks PRD into epic + story issues with priority labels |
| [skill-selection](../workflows/skill-selection.md) | PRD merged to main | Fetches coding skills from `RealPage/ai-coding-toolkit` |
| [mcp-selection](../workflows/mcp-selection.md) | PRD merged to main | Configures MCP servers in the implementation workflow |
| [validation](../workflows/validation.md) | PR labeled `needs-validation` | Validates implementation against PRD acceptance criteria |
| [auto-remediation](../workflows/auto-remediation.md) | Hourly schedule / manual | Queries Elastic for errors, triages, creates issues, opens fix PRs |

> **Not included:** `implementation.md` is project-specific (references your codebase paths, test commands, and tech stack). Use the template in [agentic-workflow-template](https://github.com/RealPage/agentic-workflow-template) as a starting point.

## Feature Development Pipeline

These workflows chain together to automate the full feature lifecycle: idea → PRD → stories → implementation → validation.

```mermaid
flowchart TD
    A["Feature Idea<br/>(GitHub Issue)"] -->|"issue labeled<br/>feature-idea"| B["PRD Generation<br/>Agent writes PRD"]
    B -->|"opens PR with PRD"| C{"PRD Review<br/>& Merge"}
    C -->|"PRD merged<br/>to main"| D["Decomposition<br/>Breaks PRD into stories"]
    C -->|"PRD merged<br/>to main"| E["Skill Selection<br/>Fetches coding skills"]
    C -->|"PRD merged<br/>to main"| F["MCP Selection<br/>Configures data sources"]
    D -->|"creates issues<br/>with labels"| G["Implementation Backlog<br/>(GitHub Issues)"]
    E -->|"opens PR adding<br/>skills to .claude/"| H{"Skill & MCP<br/>PR Review"}
    F -->|"opens PR configuring<br/>mcp-servers in workflow"| H
    G -->|"issue labeled<br/>ready-for-implementation"| I["AI Implementation<br/>Agent writes code"]
    H -->|merge| I
    I -->|"opens PR<br/>with code changes"| J{"Code Review"}
    J -->|"PR labeled<br/>needs-validation"| K["Validation<br/>Tests against criteria"]
    K -->|"comments pass/fail<br/>on PR"| J
    J -->|merge| L["Done"]

    style A fill:#4a90d9,color:#fff
    style B fill:#6c5ce7,color:#fff
    style C fill:#fdcb6e,color:#333
    style D fill:#6c5ce7,color:#fff
    style E fill:#6c5ce7,color:#fff
    style F fill:#6c5ce7,color:#fff
    style G fill:#00b894,color:#fff
    style H fill:#fdcb6e,color:#333
    style I fill:#6c5ce7,color:#fff
    style J fill:#fdcb6e,color:#333
    style K fill:#6c5ce7,color:#fff
    style L fill:#00b894,color:#fff
```

## Auto-Remediation Pipeline

Discovers errors from production logs, triages them with AI, and opens fix PRs for human review.

```mermaid
flowchart LR
    EL["Elastic Logs"] -->|"scheduled<br/>hourly"| AR["Auto-Remediation<br/>Agent discovers errors"]
    AR -->|"triage +<br/>root cause"| T["Error Analysis<br/>Severity, category,<br/>suggested fix"]
    T -->|"creates issue<br/>per error"| I["GitHub Issue<br/>with root cause"]
    T -->|"implements fix<br/>per error"| PR["Pull Request<br/>with code fix"]
    PR --> R{"Human Review"}
    R -->|"approve"| M["Merge"]
    R -->|"request changes"| PR

    style EL fill:#e17055,color:#fff
    style AR fill:#6c5ce7,color:#fff
    style T fill:#6c5ce7,color:#fff
    style I fill:#00b894,color:#fff
    style PR fill:#00b894,color:#fff
    style R fill:#fdcb6e,color:#333
    style M fill:#00b894,color:#fff
```

### Auto-remediation setup

The auto-remediation workflow requires these to be configured in your repo:

| Type | Name | Description |
|------|------|-------------|
| Variable | `SERVICE_NAME` | Service name to search errors for in Elastic |
| Variable | `ELASTIC_MCP_URL` | Elastic MCP server endpoint URL |
| Secret | `ELASTIC_MCP_API_KEY` | Elastic API key for authentication |

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
