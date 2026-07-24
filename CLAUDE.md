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
| `tfs-implement-mirrored` | Every 15 min off-hour / manual with work item ID | Variant of `tfs-implement` for large repos: both clone sites start from the GitHub `tfs-mirror/*` refs (maintained by the companion `workflows/tfs-mirror.yml`, plain YAML copied into the consumer repo) and fetch only the delta from TFS. Same contract, same safe-outputs; adopt one of the two variants per team, not both |

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
- **Repo-variable naming.** `vars.*` and `secrets.*` are a single repo-global namespace shared by every workflow a consumer installs together as a suite. A variable that is *genuinely* shared config for a family of workflows keeps a bare name (e.g. `TFS_BASE`, `TFS_REPO`, `TFS_TARGET_BRANCH`, `TFS_PROJECT`, `TFS_TEAM_AREA_PATH`, `TFS_PAT` — read identically by all the `tfs-*` workflows). A variable specific to one workflow MUST carry that workflow's prefix (`TFS_MIRROR_*` for `tfs-mirror`, `TFS_REVIEW_*` for `tfs-review-pr-mirrored`, e.g. `TFS_MIRROR_BOOTSTRAP_BRANCH`, `TFS_REVIEW_MAX_AGE_DAYS`) — never reuse a bare/shared name for a different purpose. Reusing a shared name causes a silent collision when both workflows are installed in the same repo: they read the same value, so one workflow's setting corrupts the other's behavior with no error. (Purely internal values that never leave the workflow file — job/step `env:` used only inside `run:` blocks — are not in the consumer namespace and don't need a prefix.)
- The `auto-remediation` workflow requires `SERVICE_NAME` variable, `ELASTIC_MCP_URL` variable, and `ELASTIC_MCP_API_KEY` secret in the consumer repo.
- The `pme-triage` workflow requires `SF_OAUTH_CLIENT_ID` variable and `SF_OAUTH_SECRET` secret in the consumer repo (Salesforce Connected App credentials for `pmeautomation@realpage.com`).
- The `tfs-implement` workflow requires variables `TFS_BASE`, `TFS_PROJECT`, `TFS_TEAM_AREA_PATH`, `TFS_REPO`, `TFS_TARGET_BRANCH` plus secret `TFS_PAT` in the consumer repo (Anthropic auth is via WIF — no `ANTHROPIC_API_KEY`; consumers set the `ANTHROPIC_FEDERATION_RULE_ID` + `ANTHROPIC_SERVICE_ACCOUNT_ID` vars, or inherit the RealPage org default). Defaults assume `tfs.realpage.com`; consumers on a different TFS / Azure DevOps host must override `network.allowed` in their stub. The workflow uses a three-phase architecture: a deterministic pre-agent step claims/clones (PAT scoped), the agent edits and emits a format-patch (no PAT), and safe-output handler jobs `tfs-finalize-pull-request` / `tfs-record-failure` mediate all TFS writes — so `strict: true` and the agent prompt has no TFS REST calls. The clone path is a direct TFS clone: the claim step shallow-clones (`--depth=1 --single-branch`) just the target branch tip for the agent's workspace, and the finalize handler clones the target branch with full history (so it can branch from the snapshotted `base_sha`). TFS is the only external git host the workflow talks to.
- The `tfs-implement-mirrored` workflow is a variant of `tfs-implement` for large repos where the direct TFS clone is the run-time bottleneck. Same variables, secret, architecture, and safe-outputs; the only difference is the clone path: both clone sites clone the GitHub mirror ref `tfs-mirror/<target-branch>` (via the read-only `GITHUB_TOKEN`) and then fetch only the delta from TFS. It REQUIRES the companion `workflows/tfs-mirror.yml` — plain GHA YAML that `gh aw add` does not distribute; consumers copy it into `.github/workflows/` manually. The mirror is transport only: `base_sha` and all ancestry checks reference the freshly fetched TFS tip, and mirrored SHAs are byte-identical to TFS (force-push, one-way, never merged). GitHub `main` in the consumer repo holds only workflow files; recommend a ruleset blocking human pushes to `tfs-mirror/**`. Teams adopt exactly one of the two tfs-implement variants.
- `implementation.md` is intentionally NOT shared — it is project-specific and lives only in consumer repos.
