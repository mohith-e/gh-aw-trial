# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A library of reusable GitHub Agentic Workflows (gh-aw) for automating the software development lifecycle with Claude-powered agents. Consumer repos import these workflows via remote imports — no file copying needed.

This repo contains **no application code, no build system, no tests**. It is entirely markdown-based workflow definitions and documentation.

## Repository Structure

- `workflows/` — The canonical workflow definitions imported by consumer repos. **This is the primary source of truth.**
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
| `fortify-triage` | Fortify SAST scan completes / weekly / manual | Pulls Fortify on Demand findings, creates one issue per critical/high vulnerability with remediation guidance |
| `fortify-fix` | Issue labeled `fortify-fix` | Reads a Fortify vulnerability issue, fixes the code, opens a focused PR linked to the issue |
| `implement-issue` | Issue labeled `agent:implement` | Reads an issue, discovers the project's stack, writes code and tests, runs validation, and opens a PR with a self-review |
| `pme-triage` | Every 6 hours / manual | Fetches PMEs from Salesforce, cross-references GitHub Issues, creates issues for untracked PMEs |
| `agent-generate-tests` | PR labeled `agent:tests` | Generates tests for the PR's new behavior and pushes them back to the PR branch. Tests-only — never modifies source or existing tests. See also upstream `daily-test-improver` for scheduled, incremental coverage improvement across the whole repo |
| `fix-failing-tests` | CI failure on default branch / issue labeled `agent:fix-tests` / manual | Reads failing tests on `main`, diagnoses the root cause, fixes code or tests, opens a fix PR with self-review. Pairs with upstream `pr-fix` (open PRs) and `ci-doctor` (diagnosis only) |
| `agent-refactor` | Issue or PR labeled `agent:refactor` | Developer-directed, behavior-preserving refactor of one area per run. Modes: targeted (area in issue body), sweep (agent picks an area), PR (refactor the PR's diff) |
| `agent-review-pr` | PR opened or reopened | Auto AI code review — analyzes the diff for correctness, security, and repo patterns; leaves up to 8 inline comments and submits one summary review with a per-dimension score |
| `tfs-implement` | Every 15 min off-hour / manual with work item ID | Implements one Azure DevOps (TFS) work item per run — claims via tag state machine, shallow-clones the target branch directly from TFS, writes code in an `agent/wi-*` branch, pushes back to TFS, and opens a PR in TFS with PR review notes. Reusable across teams; configure via repo variables |

## How Consumer Repos Use This

Consumer repos create thin stubs in `.github/workflows/` that declare triggers/permissions and import shared logic:

```yaml
---
on:
  issues:
    types: [opened, labeled]
imports:
  - RealPage/agentic-workflows/workflows/prd-generation.md@v0.1.0
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

## Working with gh-aw

When creating, updating, debugging, or compiling workflows using the `gh aw` CLI, defer to the agent defined in `.github/agents/agentic-workflows.agent.md`. It routes to the appropriate specialized prompt (create, update, debug, upgrade, etc.) and references the canonical gh-aw documentation.

Key commands:
- `gh aw init` — initialize a repo for agentic workflows
- `gh aw compile [workflow-name]` — generate/validate lock files
- `gh aw logs [workflow-name]` — view workflow run logs
- `gh aw audit <run-id>` — audit a specific run

## Key Conventions

- Workflows assume consumer repos have a `CLAUDE.md` describing their project context and a PRD template at `docs/prds/templates/prd-template.md`.
- The `auto-remediation` workflow requires `SERVICE_NAME` variable, `ELASTIC_MCP_URL` variable, and `ELASTIC_MCP_API_KEY` secret in the consumer repo.
- The `pme-triage` workflow requires `SF_OAUTH_CLIENT_ID` variable and `SF_OAUTH_SECRET` secret in the consumer repo (Salesforce Connected App credentials for `pmeautomation@realpage.com`).
- The `tfs-implement` workflow requires variables `TFS_BASE`, `TFS_PROJECT`, `TFS_TEAM_AREA_PATH`, `TFS_REPO`, `TFS_TARGET_BRANCH` plus secrets `TFS_PAT` and `ANTHROPIC_API_KEY` in the consumer repo. Defaults assume `tfs.realpage.com`; consumers on a different TFS / Azure DevOps host must override `network.allowed` in their stub. The workflow uses a three-phase architecture: a deterministic pre-agent step claims/clones (PAT scoped), the agent edits and emits a format-patch (no PAT), and safe-output handler jobs `tfs-finalize-pull-request` / `tfs-record-failure` mediate all TFS writes — so `strict: true` and the agent prompt has no TFS REST calls. The clone path is a direct TFS clone: the claim step shallow-clones (`--depth=1 --single-branch`) just the target branch tip for the agent's workspace, and the finalize handler clones the target branch with full history (so it can branch from the snapshotted `base_sha`). TFS is the only external git host the workflow talks to.
- `implementation.md` is intentionally NOT shared — it is project-specific and lives only in consumer repos.
