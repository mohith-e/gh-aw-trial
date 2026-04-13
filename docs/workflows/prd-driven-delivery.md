# PRD-Driven Delivery

Automates the full feature lifecycle — from idea to validated PR — by chaining multiple workflows together through GitHub events.

## Pipeline

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

## Workflows in the Pipeline

Each stage is a separate workflow. They chain through GitHub events — one workflow's output (a merged PR, a labeled issue) triggers the next.

### 1. PRD Generation

**Trigger:** Issue labeled `feature-idea`

Reads the issue description and generates a Product Requirements Document using the template at `docs/prds/templates/prd-template.md`. Opens a PR with the draft PRD for human review.

```bash
gh aw add-wizard RealPage/agentics/workflows/prd-generation.md@v0.2.0
```

### 2. Decomposition

**Trigger:** PRD merged to main

Breaks the PRD into an epic and individual stories as GitHub Issues. Stories are prioritized (P0/P1/P2) based on the PRD's classification and labeled for implementation. P0 stories with no dependencies get labeled `ready-for-implementation` automatically.

```bash
gh aw add-wizard RealPage/agentics/workflows/prd-decomposition.md@v0.2.0
```

### 3. Skill Selection

**Trigger:** PRD merged to main (runs in parallel with decomposition)

Analyzes the PRD's technical requirements and pulls relevant coding skills from [RealPage/ai-coding-toolkit](https://github.com/RealPage/ai-coding-toolkit) into your repo's `.claude/skills/` directory. These skills give implementation agents best practices for your stack.

```bash
gh aw add-wizard RealPage/agentics/workflows/skill-selection.md@v0.2.0
```

### 4. MCP Selection

**Trigger:** PRD merged to main (runs in parallel with decomposition)

Configures MCP servers (BigQuery, Brave Search, Datadog, etc.) in your implementation workflow so agents have access to the right data sources and tools during development.

```bash
gh aw add-wizard RealPage/agentics/workflows/mcp-selection.md@v0.2.0
```

### 5. Implementation

**Trigger:** Issue labeled `agent:implement`

Use [`implement-issue`](../../workflows/implement-issue.md) as the default implementation agent — it discovers your repo's stack, test commands, and conventions at runtime so it works out of the box. Customize it for your repo once you want faster, more predictable runs (see [`docs/workflows/implement-issue.md`](implement-issue.md) for upgrade prompts).

### 6. Validation

**Trigger:** PR labeled `needs-validation`

Validates the implementation against the PRD's acceptance criteria. Posts a checklist on the PR showing which criteria pass or fail, with a recommendation to approve, request changes, or discuss.

```bash
gh aw add-wizard RealPage/agentics/workflows/validation.md@v0.2.0
```

## Prerequisites

Your repo needs these files for the full pipeline:

| File | Used By | Purpose |
|------|---------|---------|
| `CLAUDE.md` | All workflows | Project context, tech stack, and conventions |
| `docs/prds/templates/prd-template.md` | PRD generation | Template structure for generated PRDs |
| `.github/workflows/implementation.md` | MCP selection | Project-specific implementation workflow |

Get the PRD template:

```bash
mkdir -p docs/prds/templates
curl -sL "https://raw.githubusercontent.com/RealPage/agentics/v0.2.0/docs/prds/templates/prd-template.md" \
  -o docs/prds/templates/prd-template.md
```

## Picking a Subset

You don't need the full pipeline. Common combinations:

- **PRD generation only** — Get AI-written PRDs from feature ideas, handle the rest manually
- **PRD + decomposition** — Automate planning, implement stories yourself
- **Validation only** — Add automated acceptance testing to your existing PR flow
- **Full pipeline** — End-to-end from idea to validated PR
