# gh-aw Shared Workflows

Reusable [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/) for automating the full software development lifecycle with Claude-powered agents.

## Feature Development Pipeline

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

## Shared Workflows

These workflows are project-agnostic and can be synced into any repo:

### Feature Development

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `prd-generation.md` | Issue labeled `feature-idea` | Generate a PRD from a feature idea |
| `decomposition.md` | PRD merged to `main` | Break PRD into epic + stories |
| `skill-selection.md` | PRD merged to `main` | Fetch coding skills from ai-coding-toolkit |
| `mcp-selection.md` | PRD merged to `main` | Configure MCP servers for implementation agents |
| `validation.md` | PR labeled `needs-validation` | Validate code against PRD acceptance criteria |

### Operations

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `auto-remediation.md` | Hourly schedule + manual | Discover errors from Elastic, triage, implement fixes, open PRs |

> **Not included:** `implementation.md` is project-specific (references your codebase paths, test commands, and tech stack). Use the template in [agentic-workflow-template](https://github.com/RealPage/agentic-workflow-template) as a starting point.

### Auto-Remediation Setup

The auto-remediation workflow requires additional configuration:

| Type | Name | Description |
|------|------|-------------|
| Variable | `SERVICE_NAME` | Service name to search errors for in Elastic |
| Variable | `ELASTIC_MCP_URL` | Elastic MCP server endpoint URL |
| Secret | `ELASTIC_MCP_API_KEY` | Elastic API key for authentication |

## Usage

### New Project

Use [agentic-workflow-template](https://github.com/RealPage/agentic-workflow-template) to scaffold a new repo, then sync:

```bash
gh repo create RealPage/my-project --template RealPage/agentic-workflow-template --private
cd my-project
./scripts/sync-workflows.sh
gh aw compile
```

### Existing Project

```bash
# Download the sync script
mkdir -p scripts
gh api repos/RealPage/gh-aw-shared-workflows/contents/scripts/sync-workflows.sh \
  --jq '.content' | base64 -d > scripts/sync-workflows.sh
chmod +x scripts/sync-workflows.sh

# Pull all shared workflows
./scripts/sync-workflows.sh

# Create your project-specific implementation.md
# (see template repo for example)

# Compile and commit
gh aw compile
git add .github/workflows/ scripts/
git commit -m "Add agentic development workflows"
```

### Staying in Sync

Projects created from the template include a GitHub Actions workflow that auto-syncs weekly and opens a PR if workflows have changed. You can also sync manually:

```bash
./scripts/sync-workflows.sh
gh aw compile
```

## Contributing

1. Create a branch in this repo
2. Edit the workflow under `workflows/`
3. Test your changes by copying the workflow into a project and running `gh aw compile` + `gh aw run <workflow>`
4. Open a PR — once merged, all synced projects will pick up the change on their next sync
