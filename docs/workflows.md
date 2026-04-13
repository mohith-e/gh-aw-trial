# Workflow Reference

Detailed documentation for all agentic workflows in this repo.

## Pipelines

These are end-to-end workflows that chain multiple agents together:

- [PRD-Driven Delivery](workflows/prd-driven-delivery.md) — idea → PRD → stories → implementation → validation
- [Story-Driven Delivery](workflows/story-driven-delivery.md) — idea → opportunity → user activities → stories → implementation → validation
- [Auto-Remediation](workflows/auto-remediation.md) — errors logged → errors triaged → issue created → PR with fix
- [Fortify Remediation](workflows/fortify-remediation.md) — SAST scan completes → vulnerabilities triaged → issue per finding → PR with fix
- [PME Triage](workflows/pme-triage.md) — Salesforce PMEs fetched → cross-referenced against GitHub Issues → untracked PMEs surfaced as issues

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
| [fortify-triage](../workflows/fortify-triage.md) | Fortify SAST scan completes / weekly / manual | Pulls Fortify on Demand findings, creates one issue per critical/high vulnerability with remediation guidance |
| [fortify-fix](../workflows/fortify-fix.md) | Issue labeled `fortify-fix` | Reads the vulnerability issue, fixes the code, opens a focused PR linked to the issue |
| [implement-issue](../workflows/implement-issue.md) | Issue labeled `agent:implement` | Reads an issue, discovers the project stack, writes code and tests, runs validation, and opens a PR with a self-review. Generic crawl-tier implementation agent |
| [pme-triage](../workflows/pme-triage.md) | Every 6 hours / manual | Fetches PMEs from Salesforce, cross-references GitHub Issues, creates issues for untracked PMEs |
| [agent-generate-tests](../workflows/agent-generate-tests.md) | PR labeled `agent:tests` | Generates tests for the PR's new behavior and pushes them back to the PR branch. Tests-only — never modifies source or existing tests |
| [fix-failing-tests](../workflows/fix-failing-tests.md) | CI failure on default branch / issue labeled `agent:fix-tests` / manual | Reads failing tests on `main`, diagnoses the root cause, fixes code or tests, opens a fix PR with self-review |
| [agent-refactor](../workflows/agent-refactor.md) | Issue or PR labeled `agent:refactor` | Developer-directed, behavior-preserving refactor of one area per run. Modes: targeted (area named in issue body), sweep (agent picks an area), PR (refactor the PR's diff) |
| [agent-review-pr](../workflows/agent-review-pr.md) | PR opened or reopened | Auto AI code review — analyzes the diff for correctness, security, and repo patterns; leaves up to 8 inline comments and submits one summary review with a per-dimension score |

## Recommended Upstream Workflows

These workflows live in [`githubnext/agentics`](https://github.com/githubnext/agentics/tree/main/workflows) rather than this repo. We recommend pairing them with `fix-failing-tests` for a full test-failure remediation story. See [`docs/workflows/fix-failing-tests.md`](workflows/fix-failing-tests.md) for the "when to use which" comparison.

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| [pr-fix](https://github.com/githubnext/agentics/blob/main/workflows/pr-fix.md) | Comment `/pr-fix` on a PR | Pushes a fix directly to the PR branch when its CI is failing |
| [ci-doctor](https://github.com/githubnext/agentics/blob/main/workflows/ci-doctor.md) | Monitored `workflow_run` completes with failure | Diagnostic only — opens an issue with root-cause analysis |

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
